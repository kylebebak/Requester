import json
import os
from collections import OrderedDict
from time import time
from urllib import parse

import sublime
import sublime_plugin

from ..core.helpers import truncate


def load_history(rev=True, as_dict=False):
    """Returns list of past requests. Raises exception if history file doesn't
    exist.
    """
    history_file = sublime.load_settings("Requester.sublime-settings").get("history_file", None)
    if not history_file:
        raise KeyError

    history_path = os.path.join(sublime.packages_path(), "User", history_file)
    with open(history_path, "r") as f:
        rh = json.loads(f.read() or "{}", object_pairs_hook=OrderedDict)
    if as_dict:
        return rh
    requests = list(rh.items())
    if rev:
        requests.reverse()
    return requests


def populate_staging_view(
    view,
    index,
    total,
    request,
    method,
    url,
    code,
    ts,
    meta=None,
    file=None,
    env_string=None,
    env_file=None,
    original_request=None,
    tabname=None,
):
    """Populate staging view with historical request string/metadata."""
    from .request import response_tab_bindings, set_save_info_on_view

    view.settings().set("requester.response_view", True)
    view.settings().set("requester.history_view", True)
    view.settings().set("requester.file", file)
    view.settings().set("requester.env_string", env_string)
    set_save_info_on_view(view, original_request or request)

    config = sublime.load_settings("Requester.sublime-settings")
    max_len = int(config.get("response_tab_name_length", 32))

    meta_parts = [
        "{} {}{}".format(code, method, " ({})".format(meta) if meta else ""),
        url,
        "{}: {}/{}".format(approximate_age(ts), index + 1, total),
        file,
    ]
    meta_string = "\n".join(s for s in meta_parts if s)
    content = "{}\n\n{}\n\n{}\n".format(request, response_tab_bindings(include_delete=True), meta_string)
    view.run_command("requester_replace_view_text", {"text": content, "point": 0})

    path = parse.urlparse(url).path
    if path and path[-1] == "/":
        path = path[:-1]
    view.set_name(truncate("({}) {}: {}".format(index + 1, method, path), max_len))
    view.set_syntax_file("Packages/Requester/syntax/requester-history.sublime-syntax")
    view.set_scratch(True)


def approximate_age(from_stamp, to_stamp=None, precision=2):
    """Calculate the relative time from given timestamp to another given
    (epoch) or now.

    Taken from: <https://github.com/FichteFoll/sublimetext-filehistory>
    """
    if to_stamp is None:
        to_stamp = time()
    rem = to_stamp - from_stamp

    def divide(rem, mod):
        return rem % mod, int(rem // mod)

    def subtract(rem, div):
        n = int(rem // div)
        return n, rem - n * div

    seconds, rem = divide(rem, 60)
    minutes, rem = divide(rem, 60)
    hours, days = divide(rem, 24)
    years, days = subtract(days, 365)
    months, days = subtract(days, 30)
    weeks, days = subtract(days, 7)

    magnitudes = []
    first = None
    values = locals()
    for i, magnitude in enumerate(("years", "months", "weeks", "days", "hours", "minutes", "seconds")):
        v = int(values[magnitude])
        if v == 0:
            continue
        s = "{} {}".format(v, magnitude)
        if v == 1:  # strip plural s
            s = s[:-1]
        # handle precision limit
        if first is None:
            first = i
        elif first + precision <= i:
            break
        magnitudes.append(s)

    age = ", ".join(magnitudes)
    return (age or "0 seconds") + " ago"


class RequesterHistoryCommand(sublime_plugin.WindowCommand):
    """Loads request history from file, and populates quick panel with list of
    requests in reverse chronological order. If a request is chosen from quick
    panel, stage request.
    """

    def run(self):
        try:
            self.requests = load_history()
        except Exception as e:
            print(e)
            return

        entries = [self.get_entry_parts(req) for req in self.requests]
        self.window.show_quick_panel(
            [e for e in entries if e is not None], self.on_done  # in case, e.g., schema has changed
        )

    def get_entry_parts(self, req):
        """Display request and other properties for each entry."""
        tabname = req[1].get("tabname", None)
        meta = req[1].get("meta", None)

        header = "{}{}: {}".format(req[1]["method"].upper(), " ({})".format(meta) if meta else "", req[1]["url"])
        if tabname:
            header = "{} - {}".format(tabname, header)

        try:  # in case, e.g., schema has changed
            seconds = time() - req[1]["ts"]
            pad = chr(8203) * min(round(pow(round(seconds / 60), 0.4)), 150)
            return [
                pad + truncate(header, 100),
                approximate_age(req[1]["ts"]),
                str(req[1]["code"]),
                req[1]["file"] or "?",
            ]
        except:
            return None

    def on_done(self, index):
        """Callback invokes request chosen from quick panel."""
        if index < 0:  # e.g. user presses escape
            return

        params_dict = self.requests[index][1]
        total = len(self.requests)
        reversed_index = total - index - 1
        view = self.window.new_file()
        view.settings().set("requester.request_history_index", reversed_index)
        populate_staging_view(view, index, total, **params_dict)


class RequesterOpenRequestHistoryFileCommand(sublime_plugin.WindowCommand):
    """Open request history file in read only view."""

    def run(self):
        history_file = sublime.load_settings("Requester.sublime-settings").get("history_file", None)
        if not history_file:
            raise KeyError
        view = self.window.open_file(os.path.join(sublime.packages_path(), "User", history_file))
        view.set_read_only(True)


class RequesterPageRequestHistoryCommand(sublime_plugin.TextCommand):
    """`TextCommand` to page through and stage previously executed requests. Can
    only be executed from response view. Replaces text in view with request string
    and response metadata.
    """

    def run(self, edit, pages):
        view = self.view
        if not view.settings().get("requester.response_view", False):
            return
        reqs = load_history(rev=False)
        index = view.settings().get("requester.request_history_index", len(reqs) - 1)
        total = len(reqs)

        if total == 0:
            return

        index += pages
        if index < 0:
            index = 0
        if index >= len(reqs):
            index -= 1

        try:
            params_dict = reqs[index][1]
        except IndexError as e:
            sublime.error_message("RequestHistory Error: {}".format(e))
            return
        view.settings().set("requester.request_history_index", index)
        populate_staging_view(view, total - index - 1, total, **params_dict)


class RequesterDeleteRequestHistoryCommand(sublime_plugin.TextCommand):
    """`TextCommand` to delete a staged request from history, using the same key
    used to persist requests. Locks access to `delete_request`, using same lock
    that protects `persist_requests`.
    """

    def run(self, edit):
        from . import RequestCommandMixin

        with RequestCommandMixin.LOCK:
            delete_request(self.view)
            self.view.run_command("requester_page_request_history", {"pages": -1})


def delete_request(view, history_path=None):
    """Delete request in this staging `view` from request history."""
    if not view.settings().get("requester.response_view") or not view.settings().get("requester.history_view"):
        return

    reqs = load_history(rev=False)
    index = view.settings().get("requester.request_history_index", None)
    if index is None:
        sublime.error_message("History Error: request index doesn't exist")
        return

    try:
        params_dict = reqs[index][1]
    except IndexError as e:
        sublime.error_message("RequestHistory Error: {}".format(e))
        return

    request = params_dict["request"]
    file = params_dict["file"]
    key = "{};;{}".format(request, file) if file else request
    rh = load_history(as_dict=True)
    try:
        del rh[key]
    except KeyError:
        pass
    try:
        del rh[request]  # also delete identical requests not sent from any file
    except KeyError:
        pass

    config = sublime.load_settings("Requester.sublime-settings")
    history_file = config.get("history_file", None)
    if not history_path:
        history_path = os.path.join(sublime.packages_path(), "User", history_file)
    write_json_file(rh, history_path)


class RequesterMoveRequesterFileCommand(sublime_plugin.TextCommand):
    """Moves requester file in active view to new path, and updates request
    history for all requests sent from this file. Locks access to
    `move_requester_file`, using same lock that protects `persist_requests`.
    """

    def run(self, edit):
        old_path = self.view.file_name()
        if not old_path:
            return

        def on_done(new_path):
            from . import RequestCommandMixin

            with RequestCommandMixin.LOCK:
                move_requester_file(self.view, old_path, new_path)

        self.view.window().show_input_panel("New path for requester file:", old_path, on_done, None, None)


def move_requester_file(view, old_path, new_path):
    if os.path.exists(new_path):
        sublime.error_message("Move Requester File Error: `{}` already exists".format(new_path))
        return
    try:
        os.rename(old_path, new_path)
    except Exception:
        sublime.error_message(
            "Move Requester File Error: you couldn't move file to `{}`\n\n\
Remember to create the destination folder first".format(
                new_path
            )
        )
        return
    window = view.window()
    window.run_command("close_file")
    window.open_file(new_path)

    rh = load_history(as_dict=True)
    for k, v in rh.items():
        if v.get("file") == old_path:
            v["file"] = new_path

    config = sublime.load_settings("Requester.sublime-settings")
    history_file = config.get("history_file", None)
    write_json_file(rh, os.path.join(sublime.packages_path(), "User", history_file))


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
