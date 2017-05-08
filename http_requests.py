import sublime, sublime_plugin

import os
import re
import imp
from collections import namedtuple
from urllib import parse

from .responses import ResponseThreadPool


Content = namedtuple('Content', 'content, point')

class RequestCommandMixin:

    def get_selections(self):
        raise NotImplementedError

    def open_response_view(self, request, response, **kwargs):
        raise NotImplementedError

    def run(self, edit):
        self.config = sublime.load_settings('http_requests.sublime-settings')
        # this method runs first, which means `self.config` is available to all methods
        env = self.get_env(
            self.view.settings().get('http_requests.requests_file_path', None)
        )
        selections = self.get_selections()
        self.display_responses(selections, env)

    def get_env(self, requests_file_path=None):
        """Imports the user-specified `env_file` and returns an env dictionary.

        http://stackoverflow.com/questions/67631/how-to-import-a-module-given-the-full-path
        """
        requests_file_path = requests_file_path or self.view.file_name()
        requests_file_dir = os.path.dirname( requests_file_path )

        scope = {'env_file': self.config.get('env_file')} # default `env_file` read from settings
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requests file
        with open(requests_file_path) as f:
            for line in f:
                m = p.match(line) # matches only at beginning of string
                if m:
                    try:
                        exec(line, scope) # add `env_file` to `scope` dict
                    except:
                        pass
                    break # stop looking after first match

        env_file = scope.get('env_file')
        if env_file:
            env_file_path = os.path.join( requests_file_dir, str(env_file) )
            try:
                env = imp.load_source('http_requests.env', env_file_path)
            except (FileNotFoundError, SyntaxError) as e:
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
        content = r.text

        before_content_items = [' '.join(request.split()), header, '[cmd+r] replay request', headers]
        before_content = '\n\n'.join(before_content_items)

        return Content(before_content + '\n\n' + content, len(before_content) + 2)

    def display_responses(self, selections, env=None, is_done=False):
        """Make requests concurrently using a `ThreadPool`. Display responses as
        they are returned.

        Thread pool runs on alternate thread, and is inspected at regular
        intervals to remove completed responses and display them, or display any
        errors for a given request.
        """
        if not hasattr(self, '_pool'):
            self._pool = ResponseThreadPool(selections, env) # pass along env vars to thread pool
            self._errors = []
            sublime.set_timeout_async(lambda: self._pool.run(), 0) # run on an alternate thread
            sublime.set_timeout(lambda: self.display_responses(selections), 100)

        else: # this code has to be thread-safe...
            if self._pool.is_done:
                is_done = True

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
                return
            sublime.set_timeout(lambda: self.display_responses(selections), 100)

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


class RequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests concurrently from requests file and open multiple response
    views.
    """

    def get_selections(self):
        """Gets multiple selections. If nothing is highlighted, cursor's current
        line is taken as selection.
        """
        view = self.view
        selections = []
        for region in view.sel():
            if not region.empty():
                selections.append( view.substr(region) )
            else:
                selections.append( view.substr(view.line(region)) )
        selections = [self.prepare_selection(s) for s in selections]
        return selections

    def open_response_view(self, request, response, num_selections):
        """Create a response view and insert response content into it.
        """
        window = self.view.window()
        sheet = window.active_sheet()

        view = window.new_file()
        view.set_scratch(True)
        view.settings().set('http_requests.response_view', True)
        # this setting allows keymap to target response views separately
        view.settings().set('http_requests.requests_file_path', self.view.file_name())
        view.set_name('{}: {}'.format(
            response.request.method, parse.urlparse(response.url).path
        )) # short but descriptive, to facilitate navigation between response tabs using Goto Anything

        content = self.get_response_content(request, response)
        view.run_command('http_requests_replace_view_text',
                         {'text': content.content, 'point': content.point})
        self.set_syntax(view, response)

        if num_selections > 1:
            # keep focus on requests view if multiple requests are being executed
            window.focus_sheet(sheet)


class ReplayRequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Replay a request from a response view.
    """

    def get_selections(self):
        """Returns only one selection, the one on the first line.
        """
        return [self.prepare_selection(
            self.view.substr( self.view.line(0) ), False
        )]

    def open_response_view(self, request, response, **kwargs):
        """Overwrites content in current view.
        """
        content = self.get_response_content(request, response)
        self.view.run_command('http_requests_replace_view_text',
                             {'text': content.content, 'point': content.point})
        self.set_syntax(self.view, response)
