import sublime
import sublime_plugin

import os

import requests

from .core.helpers import truncate


class RequesterDownloadCommand(sublime_plugin.ApplicationCommand):
    """Download a file to disk without opening a response view.
    """
    CANCELLED = False

    def run(self, args, kwargs):
        # cache for setting status on this view later, in case focus changes to
        # different view while env is executed and initial request is run
        RequesterDownloadCommand.CANCELLED = False
        view = sublime.active_window().active_view()
        filename = kwargs.pop('filename')
        sublime.set_timeout_async(
            lambda: self.run_initial_request(args, kwargs, filename, view), 0
        )

    def run_initial_request(self, args, kwargs, filename, view):
        try:
            r = requests.get(*args, stream=True, **kwargs)
        except Exception as e:
            sublime.error_message('Download Error: {}'.format(e))
            return

        if r.status_code != 200:
            sublime.error_message(
                'Download Error: response status code is not 200\n\n{}'.format(truncate(r.text, 500))
            )
            if sublime.load_settings('Requester.sublime-settings').get('only_download_for_200', True):
                return
        sublime.set_timeout_async(lambda: self.download_file(r, filename, view), 0)

    def download_file(self, response, filename, view):
        length = int(response.headers.get('content-length') or 0)
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
            with open(filename, 'xb') as f:  # don't overwrite file if it already exists
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
