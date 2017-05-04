import sublime, sublime_plugin

import os
import re

import requests
from requests import delete, get, head, options, patch, post, put


class RequestCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.config = sublime.load_settings('http_requests.sublime-settings')
        self.import_variables()
        selections = self.get_selections()
        for s in selections:
            response = eval(s)
            print(response.text)

    def import_variables(self):
        requests_file_path = self.view.file_name()
        requests_file_dir = os.path.dirname( requests_file_path )

        globals()['env_file'] = self.config.get('env_file') # default `env_file` read from settings
        p = re.compile('\s*env_file\s*=.*') # `env_file` can be overridden from within requests file
        with open(requests_file_path) as f:
            for line in f:
                m = p.match(line)
                if m:
                    exec(line, globals())
                    break

        env_file = globals().get('env_file')
        if env_file:
            env_file_path = os.path.join( requests_file_dir, env_file )
            with open(env_file_path) as f:
                exec(f.read(), globals())

    def get_selections(self):
        view = self.view
        selections = []
        for region in view.sel():
            if not region.empty():
                selections.append( view.substr(region) )
            else:
                selections.append( view.substr(view.line(region)) )
        return selections

