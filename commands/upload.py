import sublime
import sublime_plugin

import os

import requests

from .request import RequestsMixin
from ..core.helpers import absolute_path, get_transfer_indicator
from ..core.responses import Response
from ..core import RequestCommandMixin


def read_in_chunks(f, chunk_size=1024, handle_read=None):
    """Lazy function (generator) to read a file piece by piece.
    """
    chunk_count = 0
    while True:
        if Upload.CANCELLED:
            break
        chunk_count += 1
        data = f.read(chunk_size)
        if not data:
            break
        if handle_read:
            handle_read(chunk_count, chunk_size)
        yield data


class Upload(RequestsMixin, RequestCommandMixin):
    """Upload a file using streaming, i.e. without reading the file into memory.
    Optionally used chunked transfer encoding.
    """
    CANCELLED = False

    def __init__(self, req, filename, upload):
        Upload.CANCELLED = False
        self.config = sublime.load_settings('Requester.sublime-settings')
        self.view = sublime.active_window().active_view()
        self.upload_file(req, filename, upload)

    def upload_file(self, req, filename, upload):
        method, args, kwargs = req.method, req.args, req.kwargs
        filename = absolute_path(filename, self.view)
        if filename is None:
            sublime.error_message('Upload Error: requester file must be saved to use relative path')
            return
        basename = os.path.basename(filename)
        uploaded = 0

        try:
            filesize = os.path.getsize(filename)
        except Exception as e:
            sublime.error_message('Upload Error: {}'.format(e))

        def handle_read(chunk_count, chunk_size):
            nonlocal uploaded
            uploaded = chunk_count * chunk_size
            self.view.set_status('requester.upload', 'Requester Upload: {}'.format(
                get_transfer_indicator(basename, uploaded, filesize)
            ))

        try:
            with open(filename, 'rb') as f:
                requests_method = getattr(requests, method.lower())
                if upload == 'streamed':
                    uploaded = filesize
                    self.view.set_status('requester.upload', 'Requester Upload: Streaming.....')
                    res = requests_method(*args, data=f, **kwargs)
                elif upload == 'chunked':
                    res = requests_method(*args, data=read_in_chunks(f, handle_read=handle_read), **kwargs)
        except Exception as e:
            sublime.error_message('Upload Error: {}'.format(e))
            return
        finally:
            self.view.set_status('requester.upload', '')

        if self.CANCELLED and upload == 'chunked':  # streamed uploads can't be cancelled
            self.view.set_status('requester.upload', 'Requester Upload Cancelled: {}, {}kB uploaded'.format(
                filename, uploaded//1024))
        else:
            self.view.set_status('requester.upload', 'Requester Upload Completed: {}, {}kB uploaded'.format(
                filename, uploaded//1024))
        response = Response(req, res, None)
        self.handle_response(response)
        self.handle_responses([response])
        self.persist_requests([response])


class RequesterCancelUploadsCommand(sublime_plugin.ApplicationCommand):
    """Cancel all outstanding uploads.
    """
    def run(self):
        Upload.CANCELLED = True
