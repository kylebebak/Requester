from concurrent import futures
from collections import namedtuple

requests = __import__('requests')


Response = namedtuple('Response', 'selection, response')

class ResponseThreadPool:

    MAX_WORKERS = 10

    @staticmethod
    def get_response(selection, env=None):
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
        self.is_done = True
