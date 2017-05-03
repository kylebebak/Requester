import sublime, sublime_plugin

import requests
from requests import delete, get, head, options, patch, post, put


class RequestCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.import_variables()
        request = self.view.substr(self.view.line(self.view.sel()[0]))
        response = eval(request)
        print(response.text)

    def import_variables(self):
        with open('/Users/kylebebak/GoogleDrive/Code/Config/ST/Packages/http_requests/_request_variables.py') as f:
            exec(f.read(), globals())
