import sublime
import sublime_plugin

import os

import requests

from ..core.helpers import absolute_path, get_transfer_indicator


def read_in_chunks(f, chunk_size=1024*10, handle_read=None):
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


class RequesterUploadCommand(sublime_plugin.ApplicationCommand):
    """Upload a file using streaming, i.e. without reading the file into memory.
    Optionally used chunked transfer encoding.
    """
    CANCELLED = False

    def run(self, args, kwargs, filename, method):
        RequesterUploadCommand.CANCELLED = False
        view = sublime.active_window().active_view()
        sublime.set_timeout_async(lambda: self.upload_file(args, kwargs, filename, method, view), 0)

    def upload_file(self, args, kwargs, filename, method, view):
        filename = absolute_path(filename, view)
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
            view.set_status('requester.upload', 'Requester Upload: {}'.format(
                get_transfer_indicator(basename, uploaded, filesize)
            ))

        try:
            with open(filename, 'rb') as f:
                if method == 'streamed':
                    uploaded = filesize
                    res = requests.get(*args, data=f, **kwargs)
                elif method == 'chunked':
                    res = requests.get(*args, data=read_in_chunks(f, handle_read=handle_read), **kwargs)
        except Exception as e:
            sublime.error_message('Upload Error: {}'.format(e))
            return

        if self.CANCELLED and method == 'chunked':  # streamed uploads can't be cancelled
            view.set_status('requester.upload', 'Requester Upload Cancelled: {}, {}kB uploaded'.format(
                filename, uploaded//1024))
        else:
            view.set_status('requester.upload', 'Requester Upload Completed: {}, {}kB uploaded'.format(
                filename, uploaded//1024))
        print(res)


class RequesterCancelUploadsCommand(sublime_plugin.ApplicationCommand):
    """Cancel all outstanding uploads.
    """
    def run(self):
        RequesterUploadCommand.CANCELLED = True
