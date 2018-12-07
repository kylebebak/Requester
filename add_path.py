import sys
import os


class add_path():
    def __init__(self, *parts):
        self.path = os.path.normpath(os.path.join(*parts))

    def __enter__(self):
        sys.path.insert(0, self.path)

    def __exit__(self, exc_type, exc_value, traceback):
        while True:
            try:
                sys.path.remove(self.path)
            except ValueError:
                break
