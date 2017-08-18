import sublime
import sublime_plugin

import os

import requests

from .request import RequesterCommand
from ..core.helpers import truncate, absolute_path, get_transfer_indicator
from ..core.responses import Response, prepare_request


class RequesterDownloadCommand(RequesterCommand):
    """Download a file to disk without opening a response view.
    """
    CANCELLED = False

    def run(self, edit, request, args, kwargs, filename):
        RequesterDownloadCommand.CANCELLED = False
        # cache for setting status on this view later, in case focus changes to
        # different view while env is executed and initial request is run
        view = sublime.active_window().active_view()
        super().run(edit)  # evaluate and cache env on instance
        sublime.set_timeout_async(
            lambda: self.run_initial_request(request, args, kwargs, filename, view), 0
        )

    def make_requests(self, requests, env=None):
        pass

    def run_initial_request(self, request, args, kwargs, filename, view):
        try:
            res = requests.get(*args, stream=True, **kwargs)
        except Exception as e:
            sublime.error_message('Download Error: {}'.format(e))
            return

        if res.status_code != 200:
            sublime.error_message(
                'Download Error: response status code is not 200\n\n{}'.format(truncate(res.text, 500))
            )
            if sublime.load_settings('Requester.sublime-settings').get('only_download_for_200', True):
                return
        req = prepare_request(request, self._env, 0)
        if req.method.lower() != 'get':
            sublime.error_message('Download Error: use "get" method to download files')
            return
        response = Response(req, res, None)
        self.persist_requests([response])  # persist initial request before starting download
        sublime.set_timeout_async(lambda: self.download_file(res, filename, view), 0)

    def download_file(self, res, filename, view):
        filename = absolute_path(filename, view)
        if filename is None:
            sublime.error_message('Download Error: requester file must be saved to use relative path')
            return

        length = int(res.headers.get('content-length') or 0)
        chunk_size = sublime.load_settings('Requester.sublime-settings').get('chunk_size', 1024)
        chunk_size = max(int(chunk_size), 128)
        chunk_count = 0
        basename = os.path.basename(filename)

        try:
            with open(filename, 'xb') as f:  # don't overwrite file if it already exists
                for chunk in res.iter_content(chunk_size):
                    if self.CANCELLED:
                        break
                    f.write(chunk)
                    chunk_count += 1
                    view.set_status('requester.download', 'Requester Download: {}'.format(
                        get_transfer_indicator(basename, chunk_count*chunk_size, length)
                    ))
            if self.CANCELLED:
                view.set_status('requester.download', 'Requester Download Cancelled: {}'.format(filename))
                os.remove(filename)
            else:
                view.set_status('requester.download', 'Requester Download Completed: {}'.format(filename))
        except Exception as e:
            sublime.error_message('Download Error: {}'.format(e))


class RequesterCancelDownloadsCommand(sublime_plugin.ApplicationCommand):
    """Cancel all outstanding downloads.
    """
    def run(self):
        RequesterDownloadCommand.CANCELLED = True
