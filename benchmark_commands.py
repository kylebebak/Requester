import sublime
import sublime_plugin

from math import floor
from time import time

from .core import RequestCommandMixin
from .core.parsers import parse_requests


class RequesterPromptBenchmarksCommand(sublime_plugin.WindowCommand):
    """Parse `num` and `concurrency` from user input and pass them to
    `RequesterBenchmarksCommand`.
    """
    def run(self, fmt=None):
        self.window.show_input_panel('number of repetitions N:', '1', self.on_done_num, None, None)

    def on_done_num(self, text):
        try:
            self.num = int(text)
        except ValueError:
            sublime.error_message('Value Error: pass a valid integer for N')
            return
        self.window.show_input_panel('concurrency C:', '10', self.on_done_concurrency, None, None)

    def on_done_concurrency(self, text):
        try:
            self.concurrency = int(text)
        except ValueError:
            sublime.error_message('Value Error: pass a valid integer for C')
            return
        if self.window.active_view():
            self.window.active_view().run_command(
                'requester_benchmarks', {'num': self.num, 'concurrency': self.concurrency}
            )


class RequesterBenchmarksCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute each selected request `num` times, with specified `concurrency`,
    and display response time metrics.
    """
    def run(self, edit, num, concurrency):
        """Allow user to specify concurrency.
        """
        self.REPETITIONS = max(1, num)
        self.MAX_WORKERS = min(max(1, concurrency), 1000)
        self.count = 0
        self.total = 0
        self.start_time = time()
        super().run(edit)

    def get_requests(self):
        """Parses requests from multiple selections. If nothing is highlighted,
        cursor's current line is taken as selection.
        """
        view = self.view
        requests = []
        for region in view.sel():
            if not region.empty():
                selection = view.substr(region)
            else:
                selection = view.substr(view.line(region))
            try:
                requests_ = parse_requests(selection)
            except Exception as e:
                sublime.error_message('Parse Error: there may be unbalanced parentheses in calls to requests')
                print(e)
            else:
                for r in requests_:
                    requests.append(r)
        requests = requests * self.REPETITIONS
        self.total = len(requests)
        return requests

    def handle_response(self, response, num_requests):
        """Update number of responses returned, and save response time and size
        metrics in bucket according to request URL and response status code.
        """
        self.count += 1
        if floor(100 * (self.count - 1) / self.total) != floor(100 * self.count / self.total):
            self.view.set_status('requester.benchmarks', 'Requester Benchmarks: {}'.format(
                self.get_progress_indicator(self.count, self.total)
            ))

        r = response
        try:
            method, url = r.response.request.method, r.response.url
        except:
            method, url = None, None
        key = '{}: {}'.format(method, url)
        print(key)

    def handle_responses(self, responses):
        elapsed = time() - self.start_time
        print('{}s elapsed'.format(elapsed))

    @staticmethod
    def get_progress_indicator(count, total, spaces=50):
        if not total:
            return '?'
        spaces_filled = int(spaces * count/total)
        return '{} requests, [{}] {} completed'.format(
            total, '·'*spaces_filled + ' '*(spaces-spaces_filled-1), count
        )
