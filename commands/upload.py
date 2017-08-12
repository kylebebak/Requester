import sublime
import sublime_plugin

import os

import requests

from .request import RequesterCommand
from ..core.helpers import absolute_path, get_transfer_indicator
from ..core.responses import Response, prepare_request


def read_in_chunks(f, chunk_size=1024, handle_read=None):
    """Lazy function (generator) to read a file piece by piece.
    """
    chunk_count = 0
    while True:
        if RequesterUploadCommand.CANCELLED:
            break
        chunk_count += 1
        data = f.read(chunk_size)
        if not data:
            break
        if handle_read:
            handle_read(chunk_count, chunk_size)
        yield data


class RequesterUploadCommand(RequesterCommand):
    """Upload a file using streaming, i.e. without reading the file into memory.
    Optionally used chunked transfer encoding.
    """
    CANCELLED = False

    def run(self, edit, request, method, args, kwargs, filename, upload):
        RequesterUploadCommand.CANCELLED = False
        super().run(edit)
        sublime.set_timeout_async(
            lambda: self.upload_file(request, method, args, kwargs, filename, upload), 0)

    def make_requests(self, requests, env=None):
        pass

    def upload_file(self, request, method, args, kwargs, filename, upload):
        filename = absolute_path(filename, self.view)
        if filename is None:
            sublime.error_message('Upload Error: requester file must be saved to use relative path')
            return
        basename = os.path.basename(filename)
        uploaded = 0

        try:
            filesize = os.path.getsize(filename)
        except:
            return

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
        req = prepare_request(request, self._env, 0)
        response = Response(req, res, None)
        self.handle_response(response)
        self.handle_responses([response])
        self.persist_requests([response])


class RequesterCancelUploadsCommand(sublime_plugin.ApplicationCommand):
    """Cancel all outstanding uploads.
    """
    def run(self):
        RequesterUploadCommand.CANCELLED = True
