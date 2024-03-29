import imp
import json
import os
import re
import sys
from collections import OrderedDict
from queue import Queue
from threading import Lock, Thread
from time import time

import sublime

from ..add_path import add_path
from .helpers import is_auxiliary_view
from .responses import ResponseThreadPool, prepend_library


class RequestCommandMixin:
    """This mixin is the motor for parsing an env, executing requests in parallel
    in the context of this env, invoking activity indicator methods, and invoking
    response handling methods. These methods can be overridden to control the
    behavior of classes that inherit from this mixin.

    It must be mixed in to classes that also inherit from
    `sublime_plugin.TextCommand`.
    """

    REFRESH_MS = 100  # period of checks on async operations, e.g. requests
    ACTIVITY_SPACES = 9  # number of spaces in activity indicator
    MAX_WORKERS = 10  # default request concurrency
    RESPONSE_POOLS = Queue()
    MAX_NUM_RESPONSE_POOLS = 10  # up to N response pools can be stored
    LOCK = Lock()  # this lock is shared among all instances

    def get_requests(self):
        """This must be overridden to return a list of request strings.

        Hint: use `core.parsers.parse_requests`.
        """
        raise NotImplementedError('"get_requests" must be overridden to return a list of request strings')

    def show_activity_for_pending_requests(self, requests, count, activity):
        """Override this method to customize user feedback for pending requests.
        `activity` string is passed for convenience, it is generated by
        `get_activity_indicator`.
        """

    def handle_response(self, response):
        """Override this method to handle a response from a single request. This
        method is called as each response is returned.
        """

    def handle_responses(self, responses):
        """Override this method to handle responses from all requests executed.
        This method is called after all responses have been returned.
        """

    def handle_errors(self, responses):
        """Override this method to change Requester's default error handling. This
        is a convenience method that is called on all responses after they are
        returned.
        """
        errors = ["{}\n{}".format(r.req.request, r.err) for r in responses if r.err]
        if errors:
            sublime.error_message("\n\n".join(errors[:100]))
            if len(errors) > 100:
                print("Requester Errors: {} remaining errors not printed".format(len(errors) - 100))

    def run(self, edit):
        self.reset_status()
        self.config = sublime.load_settings("Requester.sublime-settings")
        # `run` runs first, which means `self.config` is available to all methods
        thread = Thread(target=self._get_env)
        thread.start()
        self._run(thread)

    def _run(self, thread, count=0):
        """Evaluate environment in a separate thread and show an activity
        indicator. Inspect thread at regular intervals until it's finished, at
        which point `make_requests` can be invoked. Return if thread times out.
        """
        REFRESH_MULTIPLIER = 2
        activity = self.get_activity_indicator(count // REFRESH_MULTIPLIER, self.ACTIVITY_SPACES)
        if count > 0:  # don't distract user with RequesterEnv status if env can be evaluated quickly
            self.view.set_status("requester.activity", "{} {}".format("RequesterEnv", activity))

        if thread.is_alive():
            timeout = self.config.get("timeout_env", None)
            if timeout is not None and count * self.REFRESH_MS / REFRESH_MULTIPLIER > timeout * 1000:
                sublime.error_message("Timeout Error: environment took too long to parse")
                self.view.set_status("requester.activity", "")
                return
            sublime.set_timeout(lambda: self._run(thread, count + 1), self.REFRESH_MS / REFRESH_MULTIPLIER)

        else:
            requests = self.get_requests()
            self.view.set_status("requester.activity", "")
            self.make_requests(requests, self._env)

    def get_env(self):
        """Computes an env from `requester.env_string` and `requester.file`
        settings. Returns a tuple containing an env dictionary and a combined env
        string.

        http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        """
        env_strings = []
        packages_path = self.config.get("packages_path", "")
        if packages_path and packages_path not in sys.path:  # makes it possible to import any Python package in env
            sys.path.append(packages_path)

        env_block, env_block_line_number, env_file, env_file_line_number = [None] * 4
        parsed = False

        if not is_auxiliary_view(self.view):  # (1) try to get env from current view
            self.view.settings().set("requester.file", self.view.file_name())
            text = self.view.substr(sublime.Region(0, self.view.size()))
            env_block, env_block_line_number, env_file, env_file_line_number = self.parse_env(text)
            parsed = True
        else:
            file = self.view.settings().get("requester.file", None)
            if file:  # (2) try to get env from saved requester file if (1) not possible
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception as e:
                    self.add_error_status_bar(str(e))
                else:
                    env_block, env_block_line_number, env_file, env_file_line_number = self.parse_env(text)
                    parsed = True

        if not parsed:  # (3) try to get env from saved env string if (1) and (2) not possible
            env_string = self.view.settings().get("requester.env_string", None)
            return self.get_env_dict_from_string(env_string), env_string

        if env_file:
            if not os.path.isabs(env_file):
                file_path = self.view.settings().get("requester.file")
                if file_path:
                    env_file = os.path.join(os.path.dirname(file_path), env_file)
            try:
                with open(env_file, "r") as f:
                    env_strings.append(f.read())
            except Exception as e:
                self.add_error_status_bar(str(e))

        env_strings.append(env_block)

        non_empty_env_strings = [s for s in env_strings if s]
        if env_block_line_number is not None and env_file_line_number is not None:
            if env_block_line_number < env_file_line_number:
                non_empty_env_strings.reverse()

        env_string = "\n\n".join(non_empty_env_strings)
        self.view.settings().set("requester.env_string", env_string)
        return self.get_env_dict_from_string(env_string), env_string

    def _get_env(self):
        """Wrapper calls `get_env`, assigns return values to instance properties."""
        self._env, self._env_string = self.get_env()

    def set_env_on_view(self, view):
        """Convenience method that copies env settings from this view to `view`."""
        for setting in ["requester.file", "requester.env_string"]:
            view.settings().set(setting, self.view.settings().get(setting, None))

    def make_requests(self, requests, env=None):
        """Make requests concurrently using a `ThreadPool`, which itself runs on
        an alternate thread so as not to block the UI.
        """
        pools = self.RESPONSE_POOLS
        pool = ResponseThreadPool(requests, env, self.MAX_WORKERS, self.view)  # pass along env vars to thread pool
        pools.put(pool)
        while pools.qsize() > self.MAX_NUM_RESPONSE_POOLS:
            old_pool = pools.get()
            old_pool.is_done = True  # don't display responses for a pool which has already been removed
        sublime.set_timeout_async(pool.run, 0)  # run on an alternate thread
        sublime.set_timeout(lambda: self.gather_responses(pool), 15)
        # small delay to show activity for requests that are returned in less than REFRESH_MS

    def _show_activity_for_pending_requests(self, requests, count):
        """Show activity indicator in status bar."""
        activity = self.get_activity_indicator(count, self.ACTIVITY_SPACES)
        self.view.set_status("requester.activity", "{} {}".format("Requester", activity))
        self.show_activity_for_pending_requests(requests, count, activity)

    def gather_responses(self, pool, count=0, responses=None):
        """Inspect thread pool at regular intervals to remove completed responses
        and handle them, and show activity for pending requests.

        Clients can handle responses and errors one at a time as they are
        completed, or as a group when they're all finished. Each response objects
        contains `request`, `response`, `error`, and `ordering` keys.
        """
        self._show_activity_for_pending_requests(pool.get_pending_requests(), count)
        is_done = pool.is_done  # cache `is_done` before removing responses from pool

        if responses is None:
            responses = []

        for _ in range(len(pool.responses)):
            response = pool.responses.popleft()
            responses.append(response)
            self.handle_response(response)

        if is_done:
            responses.sort(key=lambda response: response.req.ordering)
            self.handle_responses(responses)
            self.handle_errors(responses)
            self.persist_requests(responses)
            self.view.set_status("requester.activity", "")
            return

        sublime.set_timeout(lambda: self.gather_responses(pool, count + 1, responses), self.REFRESH_MS)

    def persist_requests(self, responses):
        """Persisting requests is NOT thread safe, so this wrapper locks access to
        `persist_requests`. Failure to do this results in corruption of the
        history file sooner or later.
        """
        with self.LOCK:
            persist_requests(self, responses)

    def add_error_status_bar(self, error):
        """Logs error to console, and adds error in status bar. Not as obtrusive
        as `sublime.error_message`.
        """
        self._status_errors.append(error)
        print("{}: {}".format("Requester Error", error))
        self.view.set_status("requester.errors", "{}: {}".format("RequesterErrors", ", ".join(self._status_errors)))

    def reset_status(self):
        """Make sure this is called _before_ `add_error_status_bar`."""
        self._status_errors = []
        self.view.set_status("requester.errors", "")
        self.view.set_status("requester.download", "")
        self.view.set_status("requester.benchmarks", "")

    @staticmethod
    def parse_env(text):
        """Parses `text` for first env block, and returns text within this env
        block.

        Also returns line numbers for start of env block and env file.
        """
        delimeter = "###env"
        in_block = False

        env_lines = []
        env_block_line_number = None
        env_file_line_number = None

        for i, line in enumerate(text.splitlines()):
            if in_block:
                if line == delimeter:
                    in_block = False
                    break
                env_lines.append(line)
            else:
                if line == delimeter:
                    env_block_line_number = i
                    in_block = True

        scope = {}
        p = re.compile(r"\s*env_file\s*=.*")
        for i, line in enumerate(text.splitlines()):
            if p.match(line):  # matches only at beginning of string
                try:
                    exec(line, scope)  # add `env_file` to `scope` dict
                    env_file_line_number = i
                except Exception as e:
                    print(e)
                break  # stop looking after first match

        env_file = scope.get("env_file")
        if not len(env_lines) or in_block:  # env block must be closed to take effect
            return None, None, env_file, env_file_line_number
        return "\n".join(env_lines), env_block_line_number, env_file, env_file_line_number

    @staticmethod
    def get_env_dict_from_string(s):
        """What it sounds like.

        http://stackoverflow.com/questions/5362771/load-module-from-string-in-python
        """
        try:
            del sys.modules["requester.env"]  # this avoids a subtle bug, DON'T REMOVE
        except KeyError:
            pass

        if not s:
            return {}

        env = imp.new_module("requester.env")
        try:
            with add_path(__file__, "..", "..", "deps"):
                exec(s, env.__dict__)
        except Exception as e:
            sublime.error_message(
                "EnvBlock Error:\n{}\n\nOpen the console to see the full environment string".format(e)
            )
            print("\nEnvString:\n```\n{}\n```".format(s))
            return {}
        else:
            return dict(env.__dict__)

    @staticmethod
    def get_activity_indicator(count, spaces):
        """Return activity indicator string."""
        cycle = count // spaces
        if cycle % 2 == 0:
            before = count % spaces
        else:
            before = spaces - (count % spaces)
        after = spaces - before
        return "[{}={}]".format(" " * before, " " * after)


def persist_requests(self, responses, history_path=None):
    """Persist up to N requests to a history file, along with the context
    needed to rebuild the env for these requests. One entry per unique
    request. Old requests are removed when requests exceed file capacity.

    Requests in history are keyed for uniqueness on request string + file.
    """
    history_file = self.config.get("history_file", None)
    if not history_file:
        return
    if not history_path:
        history_path = os.path.join(sublime.packages_path(), "User", history_file)

    try:
        with open(history_path, "r") as f:
            text = f.read() or "{}"
    except FileNotFoundError:
        open(history_path, "w").close()  # create history file if it doesn't exist
        text = "{}"
    except Exception as e:
        sublime.error_message("HistoryFile Error:\n{}".format(e))
        return
    rh = json.loads(text, object_pairs_hook=OrderedDict)

    meta = None
    for response in responses:  # insert new requests
        req, res, err = response
        if res is None:
            continue

        if "streamed" in req.skwargs:
            meta = "streamed: {}".format(req.skwargs["streamed"])
        if "chunked" in req.skwargs:
            meta = "chunked: {}".format(req.skwargs["chunked"])
        if "filename" in req.skwargs:
            meta = "download: {}".format(req.skwargs["filename"] or "./")

        tabname = req.skwargs.get("tabname")
        method, url = res.request.method, res.url
        file = self.view.settings().get("requester.file", None)
        _, original_request = self.view.settings().get("requester.binding_info", [None, None])
        if original_request is not None and prepend_library(original_request) == req.request:
            original_request = None  # don't waste space in hist file if these requests are identical

        key = "{};;{}".format(req.request, file) if file else req.request
        if key in rh:
            rh.pop(key, None)  # remove duplicate requests
        rh[key] = {
            "ts": int(time()),
            "env_string": self.view.settings().get("requester.env_string", None),
            "file": file,
            "method": method,
            "meta": meta,
            "url": url,
            "code": res.status_code,
            "request": req.request,
            "original_request": original_request,
            "tabname": tabname,
        }

    # remove oldest requests if number of requests has exceeded `history_max_entries`
    history_max_entries = self.config.get("history_max_entries", 250)
    to_delete = len(rh) - history_max_entries
    if to_delete > 0:
        keys = []
        iter_ = iter(rh.keys())
        for _ in range(to_delete):
            try:
                keys.append(next(iter_))
            except StopIteration:
                break
        for key in keys:
            try:
                del rh[key]
            except KeyError:
                pass
    write_json_file(rh, history_path)


def write_json_file(data, path):
    """Safely write `data` to file at `path`.

    https://stackoverflow.com/questions/1812115/how-to-safely-write-to-a-file
    """
    path_temp = path + ".tmp"
    path_backup = path + ".bkp"
    with open(path_temp, "w") as f:
        f.write(json.dumps(data))  # write to temp file to ensure no data loss if exception raised here
    os.rename(path, path_backup)  # create backup file in case rename is unsuccessful
    os.rename(path_temp, path)
