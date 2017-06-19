import sublime, sublime_plugin

import os

import requests


def parse_args(*args, **kwargs):
    """Used in conjunction with eval to parse args and kwargs from a string.
    """
    return args, kwargs


class RequesterDownloadCommand(sublime_plugin.ApplicationCommand):
    """Download a file to disk without opening a response view.
    """
    REQUEST = None
    ENV = None
    CANCELLED = False

    def run(self):
        RequesterDownloadCommand.CANCELLED = False
        request, env = self.REQUEST, self.ENV
        if request is None or env is None:
            return

        args, kwargs = eval('parse_args{}'.format(
            request[request.index('('):] # get args and kwargs that were passed to `requests.get`
        ))
        filename = kwargs.pop('filename')

        view = sublime.active_window().active_view() # cache for setting status on this view later
        try:
            r = requests.get(*args, stream=True, **kwargs)
        except Exception as e:
            sublime.error_message('Download Error: {}'.format(e))
            return

        if r.status_code != 200:
            sublime.error_message('Download Error: response status code != 200')
        sublime.set_timeout_async(lambda: self.download_file(r, filename, view), 0)

    def download_file(self, response, filename, view):
        length = int(response.headers.get('content-length'))
        chunk_size = sublime.load_settings('Requester.sublime-settings').get('chunk_size', 1024)
        chunk_size = max(int(chunk_size), 128)
        chunk_count = 0
        basename = os.path.basename(filename)

        if not os.path.isabs(filename):
            file_path = view.file_name()
            if file_path:
                filename = os.path.join(os.path.dirname(file_path), filename)
            else:
                sublime.error_message('Download Error: requester file must be saved to use relative path')
                return

        try:
            with open(filename, 'xb') as f: # don't overwrite file if it already exists
                for chunk in response.iter_content(chunk_size):
                    if self.CANCELLED:
                        break
                    f.write(chunk)
                    chunk_count += 1
                    view.set_status('requester.download', 'Requester Download: {}'.format(
                        self.get_download_indicator(basename, chunk_count*chunk_size, length)
                    ))
            if self.CANCELLED:
                view.set_status('requester.download', 'Requester Download Cancelled: {}'.format(filename))
                os.remove(filename)
            else:
                view.set_status('requester.download', 'Requester Download Completed: {}'.format(filename))

        except Exception as e:
            sublime.error_message('Download Error: {}'.format(e))

    @staticmethod
    def get_download_indicator(filename, downloaded, total, spaces=50):
        if not total:
            return '{}, ?'.format(filename)
        spaces_filled = int(spaces * downloaded/total)
        return '{}, [{}] {}kB'.format(
            filename, '·'*spaces_filled + ' '*(spaces-spaces_filled-1), downloaded/1024
        )


class RequesterCancelDownloadsCommand(sublime_plugin.ApplicationCommand):
    """Cancel all outstanding downloads.
    """
    def run(self):
        RequesterDownloadCommand.CANCELLED = True
