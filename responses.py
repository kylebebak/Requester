from concurrent import futures
from collections import namedtuple

requests = __import__('requests')


Response = namedtuple('Response', 'selection, response, error')

class ResponseThreadPool:
    """Allows requests to be invoked concurrently, and allows client code to
    inspect instance's responses as they are returned.
    """

    MAX_WORKERS = 10

    @staticmethod
    def get_response(selection, env=None):
        """Evaluate `selection` in context of `env`, which at the very least
        includes the `requests` module. Return `response`.
        """
        env = env or {}
        env['requests'] = requests

        response, error = None, ''
        try:
            response = eval(selection, env)
        except requests.Timeout:
            error = 'Timeout Error: the request timed out'
        except requests.ConnectionError:
            error = 'Connection Error: check your connection'
        except SyntaxError as e:
            error = '{}: {}\n\n{}'.format('Syntax Error', e,
                                          'Review properly formatted requests in README.md')
        except Exception as e:
            error = '{}: {}'.format('Other Error', e)
        else: # only check response type if no exceptions were raised
            if not isinstance(response, requests.Response):
                error = '{}: {}'.format('Type Error',
                                        'request did not return an instance of requests.Response')

        return Response(selection, response, error)

    def __init__(self, selections, env):
        self.is_done = False
        self.responses = []
        self.selections = selections
        self.pending_selections = list(selections)
        self.env = env

    def run(self):
        """Concurrently invoke `get_response` for all of instance's `selections`.
        """
        with futures.ThreadPoolExecutor(
            max_workers=min(self.MAX_WORKERS, len(self.selections))
        ) as executor:
            to_do = []
            for selection in self.selections:
                future = executor.submit(self.get_response, selection, self.env)
                to_do.append(future)

            for future in futures.as_completed(to_do):
                result = future.result()
                # `responses` and `pending_selections` are instance properties, which means
                # client code can inspect instance to read responses as they are completed
                try:
                    self.pending_selections.remove(result.selection)
                except ValueError:
                    pass
                self.responses.append(result)
        self.is_done = True
