import os

import sublime
import sublime_plugin

from ..core import RequestCommandMixin
from ..core.helpers import absolute_path, get_transfer_indicator, truncate
from ..core.responses import Response
from ..deps import requests
from .request import RequestsMixin


class Download(RequestsMixin, RequestCommandMixin):
    """Download a file to disk."""

    CANCELLED = False

    def __init__(self, req, filename):
        Download.CANCELLED = False
        self.config = sublime.load_settings("Requester.sublime-settings")
        self.view = sublime.active_window().active_view()
        self.run_initial_request(req, filename)

    def run_initial_request(self, req, filename):
        requests_method = getattr(requests, req.method.lower())
        try:
            res = requests_method(*req.args, stream=True, **req.kwargs)
        except Exception as e:
            sublime.error_message("Download Error: {}".format(e))
            return

        response = Response(req, res, None)
        self.handle_response(response)
        self.handle_responses([response])
        self.persist_requests([response])  # persist initial request before starting download

        if res.status_code != 200:
            sublime.error_message(
                "Download Error: response status code is not 200\n\n{}".format(truncate(res.text, 500))
            )
            if sublime.load_settings("Requester.sublime-settings").get("only_download_for_200", True):
                return
        self.download_file(res, filename)

    def download_file(self, res, filename):
        filename = absolute_path(os.path.expanduser(filename), self.view)  # attempts to resolve '~'
        if filename is None:
            sublime.error_message("Download Error: requester file must be saved to use relative path")
            return

        view = sublime.active_window().active_view()  # show download indicator in newly opened response tab
        length = int(res.headers.get("content-length") or 0)
        chunk_size = sublime.load_settings("Requester.sublime-settings").get("chunk_size", 1024)
        chunk_size = max(int(chunk_size), 128)
        basename = os.path.basename(filename)

        def download(filename):
            chunk_count = 0
            with open(filename, "xb") as f:  # don't overwrite file if it already exists
                for chunk in res.iter_content(chunk_size):
                    if self.CANCELLED:
                        break
                    f.write(chunk)
                    chunk_count += 1
                    view.set_status(
                        "requester.download",
                        "Requester Download: {}".format(
                            get_transfer_indicator(basename, chunk_count * chunk_size, length)
                        ),
                    )
            if self.CANCELLED:
                view.set_status("requester.download", "Requester Download Cancelled: {}".format(filename))
                os.remove(filename)
            else:
                view.set_status("requester.download", "Requester Download Completed: {}".format(filename))

        if not basename or os.path.isdir(filename):
            count, suffix = 1, ""
            filename = os.path.join(filename, res.url.split("/")[-1])
            file, extension = os.path.splitext(filename)
            extension = extension.split("?")[0]
            while True:
                try:
                    download(file + suffix + extension)
                    break
                except FileExistsError:  # retry download if filename exists
                    count, suffix = count + 1, "-{}".format(count)
                except Exception as e:
                    sublime.error_message("Download Error: {}".format(e))
                    break
        else:
            try:
                download(filename)
            except Exception as e:
                sublime.error_message("Download Error: {}".format(e))


class RequesterCancelDownloadsCommand(sublime_plugin.ApplicationCommand):
    """Cancel all outstanding downloads."""

    def run(self):
        Download.CANCELLED = True
