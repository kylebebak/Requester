import sublime

import os
import re
import imp
import json
from urllib import parse
from collections import namedtuple

from .responses import ResponseThreadPool


Content = namedtuple('Content', 'content, point')
platform = sublime.platform()

class RequestCommandMixin:

    def get_selections(self):
        raise NotImplementedError

    def open_response_view(self, request, response, **kwargs):
        raise NotImplementedError

    def run(self, edit):
        self.config = sublime.load_settings('Requester.sublime-settings')
        # `run` runs first, which means `self.config` is available to all methods
        self.set_env_from_string()
        self.set_env_from_file()
        env = self.get_env()
        selections = self.get_selections()
        self.make_requests(selections, env)

    def set_env_from_string(self):
        """Sets the `requester.env_string` setting on the view, if appropriate.
        """
        if self.view.settings().get('requester.response_view', False):
            return

        delimeter = '###env'
        in_block = False
        env_lines = []
        for line in self.view.substr( sublime.Region(0, self.view.size()) ).splitlines():
            if in_block:
                if line == delimeter:
                    in_block = False
                    break
                env_lines.append(line)
            else:
                if line == delimeter:
                    in_block = True
        if not len(env_lines) or in_block: # env block must be closed
            return
        self.view.settings().set('requester.env_string', '\n'.join(env_lines))

    def set_env_from_file(self):
        """Sets the `requester.env_file` setting on the view, if appropriate.
        """
        if self.view.settings().get('requester.response_view', False):
            return

        scope = {}
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requester file
        for line in self.view.substr( sublime.Region(0, self.view.size()) ).splitlines():
            if p.match(line): # matches only at beginning of string
                try:
                    exec(line, scope) # add `env_file` to `scope` dict
                except:
                    pass
                break # stop looking after first match

        env_file = scope.get('env_file')
        if env_file:
            env_file = str(env_file)
            if os.path.isabs(env_file):
                self.view.settings().set('requester.env_file', env_file)
            else:
                file_path = self.view.file_name()
                if file_path:
                    self.view.settings().set('requester.env_file',
                                             os.path.join(os.path.dirname(file_path), env_file))

    def get_env(self):
        """Computes an env from `requester.env_string` setting, or from
        `requester.env_file` setting. Returns an env dictionary.

        http://stackoverflow.com/questions/5362771/load-module-from-string-in-python
        http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        """
        env_string = self.view.settings().get('requester.env_string', None)
        if env_string:
            env = imp.new_module('requester.env')
            try:
                exec(env_string, env.__dict__)
            except Exception as e:
                sublime.error_message('EnvBlock Error:\n{}'.format(e))
            # return a new intance of this dict, or else its values will be reset to `None` after it's returned
            return dict(env.__dict__)

        env_file = self.view.settings().get('requester.env_file', None)
        if not env_file:
            return None

        try:
            env = imp.load_source('requester.env', env_file)
        except Exception as e:
            sublime.error_message('EnvFile Error:\n{}'.format(e))
        else:
            return vars(env)
        return None

    def make_requests(self, selections, env=None):
        """Make requests concurrently using a `ThreadPool`, which runs on an
        alternate thread.
        """
        if not hasattr(self, '_pool'):
            self._pool = ResponseThreadPool(selections, env) # pass along env vars to thread pool
            self._errors = []
            self._count = 0
            self.show_activity_for_pending_requests(selections, self._count)
            sublime.set_timeout_async(lambda: self._pool.run(), 0) # run on an alternate thread
            sublime.set_timeout(lambda: self.display_responses(selections), 100)

    def show_activity_for_pending_requests(self, selections, count):
        """Show activity indicator in status bar. Also, if there are already open
        response views waiting to display content from pending requests, show
        activity indicators in views.
        """
        activity = self.get_activity_indicator(count, 9)
        self.view.set_status('requester.activity', '{} {}'.format(
            'Requester', activity
        ))

        for selection in selections:
            for view in self.response_views_with_matching_selection(selection):
                view.run_command('requester_replace_view_text', {'text': '{}\n\n{}\n'.format(
                    selection, activity
                )})
                name = view.settings().get('requester.name')
                if not name:
                    view.set_name(activity)
                else:
                    spaces = min(9, len(name))
                    activity = self.get_activity_indicator(count, spaces)
                    extra_spaces = 4 # extra spaces because tab names don't use monospace font =/
                    view.set_name(activity.ljust( len(name) + extra_spaces ))

    def get_activity_indicator(self, count, spaces):
        """Displays an activity indicator in status bar if there are pending
        requests.
        """
        cycle = count // spaces
        if cycle % 2 == 0:
            before = count % spaces
        else:
            before = spaces - (count % spaces)
        after = spaces - before
        return '[{}={}]'.format(' ' * before, ' ' * after)

    def display_responses(self, selections):
        """Inspect thread pool at regular intervals to remove completed responses
        and display them, or display any errors for a given request.
        """
        if not hasattr(self, '_pool'):
            return
        is_done = self._pool.is_done # cache `is_done` before removing responses from pool

        while len(self._pool.responses): # remove completed responses from thread pool and display them
            r = self._pool.responses.pop(0)
            if r.error:
                self._errors.append('{}\n{}'.format(r.selection, r.error))
            else:
                self.open_response_view(r.selection, r.response, num_selections=len(selections))
            for view in self.response_views_with_matching_selection(r.selection):
                self.set_response_view_name(view, r.response)

        if is_done:
            del self._pool
            if len(self._errors):
                sublime.error_message('\n\n'.join(self._errors)) # display all errors together
            del self._errors

            self.view.set_status('requester.activity', '') # remove activity indicator from status bar
            return

        self._count += 1
        self.show_activity_for_pending_requests(self._pool.pending_selections, self._count)
        sublime.set_timeout(lambda: self.display_responses(selections), 200)

    def get_response_content(self, request, response):
        """Returns a response string that includes metadata, headers and content,
        and the index of the string at which response content begins.
        """
        r = response
        redirects = [res.url for res in r.history] # URLs traversed due to redirects
        redirects.append(r.url) # final URL

        header = '{} {}\n{}s\n{}'.format(
            r.status_code, r.reason, r.elapsed.total_seconds(),
            ' -> '.join(redirects)
        )
        headers = '\n'.join(
            [ '{}: {}'.format(k, v) for k, v in sorted(r.headers.items()) ]
        )
        try:
            json_dict = r.json()
        except:
            content = r.text
        else: # prettify json regardless of what raw response looks like
            content = json.dumps(json_dict, sort_keys=True, indent=2, separators=(',', ': '))

        replay_binding = '[cmd+r]' if platform == 'osx' else '[ctrl+r]'
        before_content_items = [
            ' '.join(request.split()), header, '{}: {}'.format('Request Headers', r.request.headers),
            '{} replay request'.format(replay_binding), headers
        ]
        cookies = r.cookies.get_dict()
        if cookies:
            before_content_items.append('{}: {}'.format('Response Cookies', cookies))
        before_content = '\n\n'.join(before_content_items)

        return Content(before_content + '\n\n' + content, len(before_content) + 2)

    def set_response_view_name(self, view, response):
        """Set name for `view` with content from `response`.
        """
        try: # short but descriptive, to facilitate navigation between response tabs using Goto Anything
            name = '{}: {}'.format(response.request.method, parse.urlparse(response.url).path)
        except:
            view.set_name( view.settings().get('requester.name') )
        else:
            view.set_name(name)
            view.settings().set('requester.name', name)

    def set_syntax(self, view, response):
        """Try to set syntax for `view` based on `content-type` response header.
        """
        if not self.config.get('highlighting', False):
            return

        view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')

    def response_views_with_matching_selection(self, selection):
        """Get all response views whose selection matches `selection`.
        """
        views = []
        for sheet in self.view.window().sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                view_selection = view.settings().get('requester.selection', None)
                if not view_selection:
                    continue
                if selection == view_selection:
                    views.append(view)
        return views

    @staticmethod
    def prepare_selection(s, timeout=None):
        """If selection is not prefixed with "{var_name}.", prefix selection with
        "requests.", because this module is guaranteed to be in the scope under
        which the selection is evaluated.

        Also, ensure request can time out so it doesn't hang indefinitely.
        http://docs.python-requests.org/en/master/user/advanced/#timeouts
        """
        s = s.strip()
        if not re.match('[\w_][\w\d_]*\.', s):
            s = 'requests.' + s

        if timeout is not None:
            timeout_string = ', timeout={})'.format(timeout)
            return s[:-1] + timeout_string
        return s
