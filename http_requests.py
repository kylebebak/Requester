import sublime, sublime_plugin

import os
import re
from collections import namedtuple
from urllib import parse
from concurrent import futures

import requests
from requests import delete, get, head, options, patch, post, put


Response = namedtuple('Response', 'selection, response')
Content = namedtuple('Content', 'content, point')

class ResponseThreadPool:

    MAX_WORKERS = 10

    @staticmethod
    def get_response(selection):
        response = Response(selection, eval(selection))
        return response

    def __init__(self, selections):
        self.is_done = False
        self.responses = []
        self.selections = selections

    def run(self):
        with futures.ThreadPoolExecutor(
            max_workers=min(self.MAX_WORKERS, len(self.selections))
        ) as executor:
            to_do = []
            for selection in self.selections:
                future = executor.submit(self.get_response, selection)
                to_do.append(future)

            for future in futures.as_completed(to_do):
                result = future.result()
                self.responses.append(result)
        self.is_done = True


class RequestCommandMixin:

    def run(self, edit):
        self.config = sublime.load_settings('http_requests.sublime-settings')
        self.import_variables(
            self.view.settings().get('http_requests.requests_file_path', None)
        )
        selections = self.get_selections()
        self.get_responses(selections)

    def import_variables(self, requests_file_path=None):
        requests_file_path = requests_file_path or self.view.file_name()
        requests_file_dir = os.path.dirname( requests_file_path )

        globals()['env_file'] = self.config.get('env_file') # default `env_file` read from settings
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requests file
        with open(requests_file_path) as f:
            for line in f:
                m = p.match(line)
                if m:
                    exec(line, globals())
                    break # stop looking after first match

        env_file = globals().get('env_file')
        if env_file:
            env_file_path = os.path.join( requests_file_dir, env_file )
            with open(env_file_path) as f:
                exec(f.read(), globals())

    def response_content(self, request, response):
        r = response
        header = '{} {}\n{}s\n{}'.format(
            r.status_code, r.reason, r.elapsed.total_seconds(), r.url
        )
        headers = '\n'.join(
            [ '{}: {}'.format(k, v) for k, v in sorted(r.headers.items()) ]
        )
        content = r.text

        before_content = '\n\n'.join(
            [' '.join(request.split()), header, '[cmd+r] replay request', headers]
        )
        return Content(before_content + '\n\n' + content, len(before_content) + 2)

    def get_responses(self, selections):
        if not hasattr(self, '_pool'):
            self._pool = ResponseThreadPool(selections)
            sublime.set_timeout_async(lambda: self._pool.run(), 0)
            sublime.set_timeout(lambda: self.get_responses(selections), 100)
        else:
            while len(self._pool.responses):
                r = self._pool.responses.pop(0)
                self.open_response_view(r.selection, r.response,
                                        num_selections=len(selections))

            if self._pool.is_done:
                del self._pool
                return
            sublime.set_timeout(lambda: self.get_responses(selections), 100)


class RequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):

    def get_selections(self):
        view = self.view
        selections = []
        for region in view.sel():
            if not region.empty():
                selections.append( view.substr(region) )
            else:
                selections.append( view.substr(view.line(region)) )
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
        content = self.response_content(request, response)
        view.run_command('http_requests_replace_view_text',
                         {'text': content.content, 'point': content.point})

        if num_selections > 1:
            window.focus_sheet(sheet) # make sure focus stays on requests sheet


class ReplayRequestCommand(RequestCommandMixin, sublime_plugin.TextCommand):

    def get_selections(self):
        return [self.view.substr( self.view.line(0) )]

    def open_response_view(self, request, response, **kwargs):
        content = self.response_content(request, response)
        self.view.run_command('http_requests_replace_view_text',
                             {'text': content.content, 'point': content.point})
