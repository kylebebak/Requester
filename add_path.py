import sys
import os


class add_path():
    def __init__(self, *parts):
        self.path = os.path.normpath(os.path.join(*parts))

    def __enter__(self):
        self.cleanup()
        sys.path.insert(0, self.path)
        return self.path

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def cleanup(self):
        try:  # guards against possibly non-deterministic bug where self is None
            path = self.path
        except Exception as e:
            print('AddPath Cleanup Error: {}'.format(e))
            return
        else:
            while path in sys.path:
                try:
                    sys.path.remove(path)
                except ValueError:
                    return
