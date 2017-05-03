import sublime, sublime_plugin

import requests
from requests import delete, get, head, options, patch, post, put


class RequestCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.import_variables()
        selections = self.get_selections()
        for s in selections:
            response = eval(s)
            print(response.text)

    def import_variables(self):
        with open('/Users/kylebebak/GoogleDrive/Code/Config/ST/Packages/http_requests/_requests_variables.py') as f:
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

