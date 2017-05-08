import sublime, sublime_plugin

import os
import re
import imp
from collections import namedtuple
from urllib import parse

from .responses import ResponseThreadPool


Content = namedtuple('Content', 'content, point')

class RequestCommandMixin:

    def run(self, edit):
        self.config = sublime.load_settings('http_requests.sublime-settings')
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
                    exec(line, scope) # add `env_file` to `scope` dict
                    break # stop looking after first match

        env_file = scope.get('env_file')
        if env_file:
            env_file_path = os.path.join( requests_file_dir, env_file )
            try:
                env = imp.load_source('http_requests.env', env_file_path)
            except FileNotFoundError:
                pass # display error
            except SyntaxError:
                pass # display error
            else:
                return vars(env)
        return None

    def get_response_content(self, request, response):
        r = response
        redirects = [res.url for res in r.history]
        redirects.append(r.url)

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
        if not hasattr(self, '_pool'):
            self._pool = ResponseThreadPool(selections, env)
            sublime.set_timeout_async(lambda: self._pool.run(), 0)
            sublime.set_timeout(lambda: self.display_responses(selections), 100)
        else: # this code has to be thread-safe...
            if self._pool.is_done:
                is_done = True

            while len(self._pool.responses):
                r = self._pool.responses.pop(0)
                self.open_response_view(r.selection, r.response,
                                        num_selections=len(selections))

            if is_done:
                del self._pool
                return
            sublime.set_timeout(lambda: self.display_responses(selections), 100)

    def set_syntax(self, view, response):
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
        s = s.strip()
        if not s.startswith('requests.'):
            s = 'requests.' + s

        if add_timeout_arg:
            timeout_string = ', timeout={})'.format(self.config.get('timeout', 30))
            return s[:-1] + timeout_string
        return s


class RequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):

    def get_selections(self):
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
        window = self.view.window()
        sheet = window.active_sheet()

        view = window.new_file()
        view.set_scratch(True)
        view.settings().set('http_requests.response_view', True)
        view.settings().set('http_requests.requests_file_path', self.view.file_name())
        view.set_name('{}: {}'.format(
            response.request.method, parse.urlparse(response.url).path
        ))
        content = self.get_response_content(request, response)
        view.run_command('http_requests_replace_view_text',
                         {'text': content.content, 'point': content.point})
        self.set_syntax(view, response)

        if num_selections > 1:
            window.focus_sheet(sheet) # make sure focus stays on requests sheet


class ReplayRequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):

    def get_selections(self):
        return [self.prepare_selection(
            self.view.substr( self.view.line(0) ), False
        )]

    def open_response_view(self, request, response, **kwargs):
        content = self.get_response_content(request, response)
        self.view.run_command('http_requests_replace_view_text',
                             {'text': content.content, 'point': content.point})
        self.set_syntax(self.view, response)
