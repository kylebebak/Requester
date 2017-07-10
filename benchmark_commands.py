import sublime
import sublime_plugin

from math import floor, ceil
from time import time
from collections import namedtuple, defaultdict

from .core import RequestCommandMixin
from .core.parsers import parse_requests


ResponseMetrics = namedtuple('ResponseMetrics', 'elapsed, sent, received, code, successful')


def header_size(headers):
    return sum(len(key) + len(value) + 4 for key, value in headers.items()) + 2


def request_response_size(response):
    """https://stackoverflow.com/questions/33064891/python-requests-urllib-monitoring-bandwidth-usage
    """
    r = response
    request_line_size = len(r.request.method) + len(r.request.path_url) + 12
    request_size = request_line_size + header_size(r.request.headers) + int(r.request.headers.get('content-length', 0))
    response_line_size = len(r.reason) + 15
    response_size = response_line_size + header_size(r.headers) + int(r.headers.get('content-length', 0))
    return (request_size, response_size)


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
    MAX_REQUESTS = 1000000

    def run(self, edit, num, concurrency):
        """Allow user to specify concurrency.
        """
        self.REPETITIONS = max(1, num)
        self.MAX_WORKERS = min(max(1, concurrency), 1000)
        self.count = 0
        self.total = 0
        self.start_time = time()
        self.metrics = defaultdict(list)
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
        if len(requests) * self.REPETITIONS > self.MAX_REQUESTS:  # avoid attempting to instantiate huge list
            self.REPETITIONS = ceil(self.MAX_REQUESTS / len(requests))
        requests = (requests * self.REPETITIONS)[:self.MAX_REQUESTS]
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

        if method and url:
            sent, received = request_response_size(r.response)
            elapsed = r.response.elapsed.total_seconds()
            self.metrics[key].append(ResponseMetrics(elapsed, sent, received, r.response.status_code, True))
        else:
            self.metrics[key].append(ResponseMetrics(0, 0, 0, None, False))

    def handle_responses(self, responses):
        """Inspect cached metrics for individual responses and extract aggregate
        metrics for all requests, and requests grouped by method and URL. Display
        metrics tab with the information.
        """
        # elapsed = time() - self.start_time
        for k, v in self.metrics.items():
            for metrics in v:
                pass

    @staticmethod
    def get_progress_indicator(count, total, spaces=50):
        if not total:
            return '?'
        spaces_filled = int(spaces * count/total)
        return '{} requests, [{}] {} completed'.format(
            total, '·'*spaces_filled + ' '*(spaces-spaces_filled-1), count
        )
