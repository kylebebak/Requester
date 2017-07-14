import sublime

import re
from concurrent import futures
from collections import namedtuple

import requests

from .parsers import PREFIX


Request = namedtuple('Request', 'request, method, url, args, kwargs, ordering')
Response = namedtuple('Response', 'request, response, error')

methods = {
    'GET': requests.get,
    'OPTIONS': requests.options,
    'HEAD': requests.head,
    'POST': requests.post,
    'PUT': requests.put,
    'PATCH': requests.patch,
    'DELETE': requests.delete,
}


def parse_args(*args, **kwargs):
    """Used in conjunction with eval to parse args and kwargs from a string.
    """
    return args, kwargs


class ResponseThreadPool:
    """Allows requests to be invoked concurrently, and allows client code to
    inspect instance's responses as they are returned.
    """
    def get_response(self, request, ordering):
        """Evaluate `request` in context of `env`, which at the very least
        includes the `requests` module. Return `response`.

        Also sets "Response" key in env to `Response` object, to provide true
        "chaining" of requests. If two requests are run serially, the second
        request can reference the response returned by the previous request.
        """
        request = self.prepare_request(request, ordering)
        self.pending_requests.append(request)

        response, error = None, ''
        if self.is_done:  # prevents further requests from being made if pool is cancelled
            return Response(request, response, error)  # check using: https://requestb.in/

        try:
            response = methods.get(request.method)(*request.args, **request.kwargs)
        except requests.Timeout:
            error = 'Timeout Error: the request timed out'
        except requests.ConnectionError:
            error = 'Connection Error: check your connection'
        except SyntaxError as e:
            error = '{}: {}\n\n{}'.format('Syntax Error', e,
                                          'Run "Requester: Show Syntax" to review properly formatted requests')
        except TypeError as e:
            error = '{}: {}'.format('Type Error', e)
        except Exception as e:
            error = '{}: {}'.format('Other Error', e)

        self.env['Response'] = response  # to allow "chaining" of serially executed requests
        return Response(request, response, error)

    def __init__(self, requests, env, max_workers):
        self.config = sublime.load_settings('Requester.sublime-settings')
        self.is_done = False
        self.responses = []
        self.requests = requests
        self.pending_requests = []
        self.env = env
        self.max_workers = max_workers

    def run(self):
        """Concurrently invoke `get_response` for all of instance's `requests`.
        """
        with futures.ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(self.requests))
        ) as executor:
            to_do = []
            for ordering, request in enumerate(self.requests):
                future = executor.submit(self.get_response, request, ordering)
                to_do.append(future)

            for future in futures.as_completed(to_do):
                result = future.result()
                # `responses` and `pending_requests` are instance properties, which means
                # client code can inspect instance to read responses as they are completed
                try:
                    self.pending_requests.remove(result.request)
                except ValueError:
                    pass
                self.responses.append(result)
        self.is_done = True

    def prepare_request(self, request, ordering):
        """Parse and evaluate args and kwargs in request string under context of
        env. These args and kwargs are later passed to call to requests in
        `get_response`.

        Also, prepare request string: if request is not prefixed with
        "{var_name}.", prefix request with "requests.", because this module is
        guaranteed to be in the scope under which the request is evaluated.
        Accepts a request string and returns a `Request` instance.

        Also, ensure request can time out so it doesn't hang indefinitely.
        http://docs.python-requests.org/en/master/user/advanced/#timeouts
        """
        req = request.strip()
        if not re.match(PREFIX, req):
            req = 'requests.' + req

        self.env['__parse_args__'] = parse_args
        index = req.index('(')
        try:
            args, kwargs = eval('__parse_args__{}'.format(req[index:]), self.env)
        except:
            args, kwargs = [], {}

        method = req[:index].split('.')[1].strip().upper()
        url = kwargs.get('url', None)
        if url is None:
            try:
                url = args[0]
            except:
                pass  # this method isn't responsible for raising exceptions

        if 'timeout' not in kwargs:
            timeout = self.config.get('timeout', None)
            kwargs['timeout'] = timeout
            req = req[:-1] + ', timeout={})'.format(timeout)  # put timeout kwarg into request string
        return Request(req, method, url, args, kwargs, ordering)
