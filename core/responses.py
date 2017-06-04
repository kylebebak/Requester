from concurrent import futures
from collections import namedtuple

requests = __import__('requests')


Response = namedtuple('Response', 'request, response, error, ordering')


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
        env = self.env or {}
        env['requests'] = requests

        response, error = None, ''
        try:
            response = eval(request, env)
        except requests.Timeout:
            error = 'Timeout Error: the request timed out'
        except requests.ConnectionError:
            error = 'Connection Error: check your connection'
        except SyntaxError as e:
            error = '{}: {}\n\n{}'.format('Syntax Error', e,
                                          'Run "Requester: Show Syntax" to review properly formatted requests')
        except Exception as e:
            error = '{}: {}'.format('Other Error', e)
        else: # only check response type if no exceptions were raised
            if not isinstance(response, requests.Response):
                error = '{}: {}'.format('Type Error',
                                        'request did not return an instance of requests.Response')
                response = None # reset response to `None` if it's not a `Response`

        if not self.env:
            self.env = {}
        self.env['Response'] = response # to allow "chaining" of serially executed requests
        return Response(request, response, error, ordering)

    def __init__(self, requests_, env, max_workers):
        self.is_done = False
        self.responses = []

        self.requests = requests_
        self.pending_requests = list(requests_)
        self.env = env
        self.max_workers = max_workers

    def run(self):
        """Concurrently invoke `get_response` for all of instance's `requests`.
        """
        with futures.ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(self.requests))
        ) as executor:
            to_do = []
            for i, request in enumerate(self.requests):
                future = executor.submit(self.get_response, request, i)
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
