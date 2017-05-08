from concurrent import futures
from collections import namedtuple

requests = __import__('requests')


Response = namedtuple('Response', 'selection, response')

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
        response = Response(selection, eval(selection, env))
        return response

    def __init__(self, selections, env):
        self.is_done = False
        self.responses = []
        self.selections = selections
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
                self.responses.append(result)
                # `responses` is an instance property, which means client code can
                # inspect this instance to read responses as they are completed
        self.is_done = True
