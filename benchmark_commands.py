import sublime
import sublime_plugin

from math import floor, ceil
from time import time
from collections import namedtuple, defaultdict

from .core import RequestCommandMixin
from .core.responses import prepare_request
from .core.parsers import parse_requests


ResponseMetrics = namedtuple('ResponseMetrics', 'elapsed, sent, received, code, success')
AggregateMetrics = namedtuple(
    'ResponseMetrics',
    'success, failure,' +
    'ok, redirect, client_error, server_error,' +
    'sent, received,' +
    'min_time, max_time, avg_time'
)


def header_size(headers):
    """https://stackoverflow.com/questions/33064891/python-requests-urllib-monitoring-bandwidth-usage
    """
    return sum(len(key) + len(value) + 4 for key, value in headers.items()) + 2


def request_response_size_kb(res):
    """https://stackoverflow.com/questions/33064891/python-requests-urllib-monitoring-bandwidth-usage
    """
    request_line_size = len(res.request.method) + len(res.request.path_url) + 12
    request_size = request_line_size + header_size(res.request.headers)\
        + int(res.request.headers.get('content-length', 0))
    response_line_size = len(res.reason) + 15
    response_size = response_line_size + header_size(res.headers) + int(res.headers.get('content-length', 0))
    return (request_size / 1024, response_size / 1024)


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
                for i, request in enumerate(requests_):
                    requests.append(prepare_request(request, self._env, i))
        if len(requests) * self.REPETITIONS > self.MAX_REQUESTS:  # avoid attempting to instantiate huge list
            self.REPETITIONS = ceil(self.MAX_REQUESTS / len(requests))
        requests = (requests * self.REPETITIONS)[:self.MAX_REQUESTS]
        self.total = len(requests)
        return requests

    def handle_response(self, response):
        """Update number of responses returned, and save response time and size
        metrics in bucket according to request URL and response status code.
        """
        self.count += 1
        if floor(100 * (self.count - 1) / self.total) != floor(100 * self.count / self.total):
            self.view.set_status('requester.benchmarks', 'Requester Benchmarks: {}'.format(
                self.get_progress_indicator(self.count, self.total)
            ))

        req, res, err = response
        key = '{}: {}'.format(req.method, req.url)
        if res is None or err:
            self.metrics[key].append(ResponseMetrics(0, 0, 0, None, False))
            return

        sent, received = request_response_size_kb(res)
        elapsed = res.elapsed.total_seconds()
        self.metrics[key].append(ResponseMetrics(elapsed, sent, received, res.status_code, True))

    def handle_responses(self, responses):
        """Invoke the real function on a different thread to avoid blocking UI.
        """
        sublime.set_timeout_async(lambda: self._handle_responses(), 0)

    def _handle_responses(self):
        """Inspect cached metrics for individual responses and extract aggregate
        metrics for all requests, and requests grouped by method and URL. Display
        metrics tab with the information.
        """
        elapsed = time() - self.start_time
        method_url_metrics = {k: self.aggregate_metrics(v) for k, v in self.metrics.items()}
        metrics = []
        for v in self.metrics.values():
            metrics += v
        all_metrics = self.aggregate_metrics(metrics)

        response_rate, transfer_rate = None, None
        if elapsed > 0:
            response_rate = all_metrics.success / elapsed
            transfer_rate = all_metrics.received / elapsed

        rates = '-- {}s, {} requests/s, {} kB/s, {} concurrency --'.format(
            round(elapsed, 3),
            round(response_rate, 2) if response_rate else '?',
            round(transfer_rate, 2) if transfer_rate else '?',
            self.MAX_WORKERS
        )
        profiles = ['{}\n{}'.format(k, self.get_profile_string(v)) for k, v in method_url_metrics.items()]
        if len(method_url_metrics) > 1:
            profiles.insert(0, self.get_profile_string(all_metrics))

        view = self.view.window().new_file()
        view.set_scratch(True)
        view.run_command('requester_replace_view_text',
                         {'text': rates + '\n\n\n' + '\n\n\n'.join(profiles) + '\n', 'point': 0})
        view.set_name('Requester Benchmarks')
        view.set_syntax_file('Packages/Requester/requester-benchmarks.sublime-syntax')

    @staticmethod
    def get_profile_string(metrics):
        """Builds the profile string for a given group of metrics.
        """
        m = metrics
        header = '{} requests, {} successful'.format(m.success + m.failure, m.success)
        codes = '{} ok, {} redirect, {} client error, {} server error'.format(
            m.ok, m.redirect, m.client_error, m.server_error
        )
        transfer = '{} kB sent, {} kB received'.format(round(m.sent, 2), round(m.received, 2))
        times = 'fastest: {}s\nslowest: {}s\naverage: {}s'.format(
            round(m.min_time, 3) if m.min_time is not None else '?',
            round(m.max_time, 3) if m.max_time is not None else '?',
            round(m.avg_time, 3) if m.avg_time is not None else '?'
        )
        return '\n'.join([header, codes, transfer, times])

    @staticmethod
    def aggregate_metrics(metrics):
        """Returns a `namedtuple` with metrics aggregated from `metrics`.
        """
        success, failure = 0, 0
        ok, redirect, client_error, server_error = 0, 0, 0, 0
        sent, received = 0, 0
        elapsed, min_time, max_time = 0, None, None

        for m in metrics:
            if m.success:
                success += 1
            else:
                failure += 1
                continue

            try:
                code = int(m.code)
            except:
                code = 500  # if server doesn't return a response code, this is a server error
            if code < 300 or code >= 600:
                ok += 1
            elif code < 400:
                redirect += 1
            elif code < 500:
                client_error += 1
            else:
                server_error += 1

            elapsed += m.elapsed
            sent += m.sent
            received += m.received

            if min_time is None:
                min_time = m.elapsed
            else:
                min_time = min(min_time, m.elapsed)
            if max_time is None:
                max_time = m.elapsed
            else:
                max_time = max(max_time, m.elapsed)

        return AggregateMetrics(success, failure, ok, redirect, client_error, server_error,
                                sent, received, min_time, max_time, elapsed / success if success else None)

    @staticmethod
    def get_progress_indicator(count, total, spaces=50):
        """For showing user how many requests are remaining.
        """
        if not total:
            return '?'
        spaces_filled = int(spaces * count/total)
        return '{} requests, [{}] {} completed'.format(
            total, '·'*spaces_filled + ' '*(spaces-spaces_filled-1), count
        )
