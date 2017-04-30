import sublime, sublime_plugin

import requests


class OpenRequestsProjectCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        r = requests.get('https://jsonplaceholder.typicode.com/posts')
        print(r.json())
