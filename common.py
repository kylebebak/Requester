import sublime

import os
import re
import imp
import json
from collections import namedtuple

from .responses import ResponseThreadPool


Content = namedtuple('Content', 'content, point')

class RequestCommandMixin:

    def get_selections(self):
        raise NotImplementedError

    def open_response_view(self, request, response, **kwargs):
        raise NotImplementedError

    def run(self, edit):
        self.config = sublime.load_settings('Requester.sublime-settings')
        # `run` runs first, which means `self.config` is available to all methods
        self.set_env()
        env = self.get_env()
        selections = self.get_selections()
        self.make_requests(selections, env)

    def set_env(self):
        """Sets the `env_file` setting on the view, if appropriate. This method is
        complex, to grant users a lot of flexibility in setting env file.
        """
        if self.view.settings().get('requester.response_view', False):
            return

        self.view.settings().set('requester.custom_env_file', False)
        scope = {'env_file': self.config.get('env_file')} # default `env_file` read from settings
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requests file
        for line in self.view.substr( sublime.Region(0, self.view.size()) ).splitlines():
            m = p.match(line) # matches only at beginning of string
            if m:
                try:
                    exec(line, scope) # add `env_file` to `scope` dict
                except:
                    pass
                self.view.settings().set('requester.custom_env_file', True)
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
        """Computes an env from `requester.env_string` setting or
        `requester.env_file` setting. Returns an env dictionary.

        http://stackoverflow.com/questions/5362771/load-module-from-string-in-python
        http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        """
        env_string = self.view.settings().get('requester.env_string', None) # this setting takes precedence
        if env_string:
            env = imp.new_module('requester.env')
            exec(env_string, env.__dict__)
            # return a new intance of this dict, or else its values will be reset to `None` after it's returned
            return dict(env.__dict__)

        env_file = self.view.settings().get('requester.env_file', None)
        if not env_file:
            return None

        try:
            env = imp.load_source('requester.env', env_file)
        except (FileNotFoundError, SyntaxError) as e:
            # don't alert user unless user specified env file from within requester file
            if self.view.settings().get('requester.custom_env_file', False):
                sublime.error_message('EnvFile Error:\n{}'.format(e))
        except Exception as e:
            sublime.error_message('Other EnvFile Error:\n{}'.format(e))
        else:
            return vars(env)
        return None

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

        before_content_items = [' '.join(request.split()), header, '[cmd+r] replay request', headers]
        before_content = '\n\n'.join(before_content_items)

        return Content(before_content + '\n\n' + content, len(before_content) + 2)

    def make_requests(self, selections, env=None):
        """Make requests concurrently using a `ThreadPool`, which runs on an
        alternate thread.
        """
        if not hasattr(self, '_pool'):
            self.set_pending(selections, True)
            self._pool = ResponseThreadPool(selections, env) # pass along env vars to thread pool
            self._errors = []
            self._count = 0
            self.view.set_status('requester.activity',
                                 self.get_activity_indicator(self._count, prefix='Requester '))
            sublime.set_timeout_async(lambda: self._pool.run(), 0) # run on an alternate thread
            sublime.set_timeout(lambda: self.display_responses(selections), 100)

    def set_pending(self, selections, status):
        for view in self.response_views_with_matching_selections(selections):
            view.settings().set('requester.pending', status)

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
            self.set_pending([r.selection], False)

        if is_done:
            del self._pool
            if len(self._errors):
                sublime.error_message('\n\n'.join(self._errors)) # display all errors together
            del self._errors

            self.view.set_status('requester.activity', '') # remove activity indicator from status bar
            return

        self._count += 1
        self.view.set_status('requester.activity',
                             self.get_activity_indicator(self._count, prefix='Requester '))
        self.show_activity_for_pending_views(selections, self._count)
        sublime.set_timeout(lambda: self.display_responses(selections), 100)

    def show_activity_for_pending_views(self, selections, count):
        for view in self.response_views_with_matching_selections(selections):
            view.set_name(self.get_activity_indicator(count))

    def response_views_with_matching_selections(self, selections):
        """Close any tab whose selection is in the current batch of selections, so
        that these tabs aren't opened twice.
        """
        for sheet in self.view.window().sheets():
            view = sheet.view()
            if view and view.settings().get('requester.response_view', False):
                selection = view.settings().get('requester.selection', None)
                if not selection:
                    continue
                if selection in selections:
                    yield view

    def get_activity_indicator(self, count, prefix='', spaces=7):
        """Displays an activity indicator in status bar if there are pending
        requests.
        """
        cycle = count // spaces
        if cycle % 2 == 0:
            before = count % spaces
        else:
            before = spaces - (count % spaces)
        after = spaces - before
        return '{}[{}={}]'.format(prefix, ' ' * before, ' ' * after)

    def set_syntax(self, view, response):
        """Try to set syntax for `view` based on `content-type` response header.
        """
        if not self.config.get('highlighting', False):
            return

        content_type = response.headers.get('content-type', None)
        if not content_type:
            return
        content_type = content_type.split(';')[0]

        content_type_syntax = {
            'application/json': 'Packages/JavaScript/JSON.sublime-syntax',
            'text/json': 'Packages/JavaScript/JSON.sublime-syntax',
            'application/xml': 'Packages/XML/XML.sublime-syntax',
            'text/xml': 'Packages/XML/XML.sublime-syntax',
            'application/xhtml+xml': 'Packages/HTML/HTML.sublime-syntax',
            'text/html': 'Packages/HTML/HTML.sublime-syntax',
        }
        syntax = content_type_syntax.get(content_type, None)
        if syntax is None:
            return
        view.set_syntax_file(syntax)

    def prepare_selection(self, s, add_timeout_arg=True):
        """Ensure selection is prefixed with "requests.", because this module is
        guaranteed to be in the scope under which the selection is evaluated.

        Also, ensure request can time out so it doesn't hang indefinitely.
        http://docs.python-requests.org/en/master/user/advanced/#timeouts
        """
        s = s.strip()
        if not s.startswith('requests.'):
            s = 'requests.' + s

        if add_timeout_arg:
            timeout_string = ', timeout={})'.format(self.config.get('timeout', 30))
            return s[:-1] + timeout_string
        return s
