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
        env = self.get_env(
            self.view.settings().get('requester.requester_file', None)
        )
        selections = self.get_selections()
        self.make_requests(selections, env)

    def get_env(self, requester_file=None):
        """Imports the user-specified `env_file` and returns an env dictionary.

        http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        """
        requester_file = requester_file or self.view.file_name()
        requester_dir = os.path.dirname(requester_file)

        from_requests_file = False
        scope = {'env_file': self.config.get('env_file')} # default `env_file` read from settings
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requests file
        with open(requester_file) as f:
            for line in f:
                m = p.match(line) # matches only at beginning of string
                if m:
                    try:
                        exec(line, scope) # add `env_file` to `scope` dict
                    except:
                        pass
                    from_requests_file = True
                    break # stop looking after first match

        env_file = scope.get('env_file')
        if env_file:
            env_file_path = os.path.join( requester_dir, str(env_file) )
            try:
                env = imp.load_source('requester.env', env_file_path)
            except (FileNotFoundError, SyntaxError) as e:
                if from_requests_file: # don't alert user unless user specified env file from within request file
                    sublime.error_message('EnvFile Error:\n{}'.format(e))
            except Exception as e:
                sublime.error_message('Other EnvFile Error:\n{}'.format(e))
            else:
                return vars(env)
        return None

    def get_response_content(self, request, response):
        """Returns a response string that includes metadata, headers and content,
        and the index of the string at which the response content begins.
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
            self._pool = ResponseThreadPool(selections, env) # pass along env vars to thread pool
            self._errors = []
            self._count = 0
            sublime.set_timeout_async(lambda: self._pool.run(), 0) # run on an alternate thread
            sublime.set_timeout(lambda: self.display_responses(selections), 100)

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
                self.open_response_view(r.selection, r.response,
                                    num_selections=len(selections))

        if is_done:
            del self._pool
            if len(self._errors):
                sublime.error_message('\n\n'.join(self._errors)) # display all errors together
            del self._errors

            self.view.set_status('requester.activity', '') # remove activity indicator from status bar
            return

        self._count += 1
        self.show_activity_indicator(self._count)
        sublime.set_timeout(lambda: self.display_responses(selections), 100)

    def show_activity_indicator(self, count):
        """Displays an activity indicator in status bar if there are pending
        requests.
        """
        spaces = 7
        cycle = count // spaces
        if cycle % 2 == 0:
            before = count % spaces
        else:
            before = spaces - (count % spaces)
        after = spaces - before
        activity = 'Requests [{}={}]'.format(' ' * before, ' ' * after)
        self.view.set_status('requester.activity', activity)

    def set_syntax(self, view, response):
        """Try to set syntax for `view` based on `content-type` response header.
        """
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
