import sublime
import sublime_plugin

import os
import json
from time import time
from collections import OrderedDict

from .request import RequesterCommand
from ..core import RequestCommandMixin
from ..core.helpers import truncate


class RequesterHistoryCommand(sublime_plugin.WindowCommand):
    """Loads request history from file, and populates quick panel with list of
    requests in reverse chronological order. If a request is chosen from quick
    panel, stage request.
    """
    def run(self):
        history_file = sublime.load_settings('Requester.sublime-settings').get('history_file', None)
        if not history_file:
            return

        history_path = os.path.join(sublime.packages_path(), 'User', history_file)
        try:
            with open(history_path, 'r') as f:
                rh = json.loads(f.read() or '{}', object_pairs_hook=OrderedDict)
        except:
            return
        self.requests = list(reversed(
            list(rh.items())
        ))

        entries = [self.get_entry_parts(req) for req in self.requests]
        self.window.show_quick_panel(
            [e for e in entries if e is not None],  # in case, e.g., schema has changed
            self.on_done
        )

    def get_entry_parts(self, req):
        """Display request and other properties for each entry.
        """
        meta = req[1].get('meta', None)
        header = '{}{}: {}'.format(
            req[1]['method'].upper(),
            ' ({})'.format(meta) if meta else '',
            req[1]['url']
        )
        try:  # in case, e.g., schema has changed
            return [
                truncate(header, 100),
                self.approximate_age(req[1]['ts']),
                str(req[1]['code']),
                req[1]['file'] or '?',
            ]
        except:
            return None

    def on_done(self, index):
        """Callback invokes request chosen from quick panel.
        """
        if index < 0:  # e.g. user presses escape
            return

        request = self.requests[index]
        params_dict = request[1]
        self.window.run_command('requester_stage_request_from_history', params_dict)

    @staticmethod
    def remove_prefix(text, prefix='requests.'):
        """Removes "requests." prefix from history entries to reduce noise.
        """
        if text.startswith(prefix):
            return text[len(prefix):]
        return text

    @staticmethod
    def approximate_age(from_stamp, to_stamp=None, precision=2):
        """Calculate the relative time from given timestamp to another given
        (epoch) or now.

        Taken from: <https://github.com/FichteFoll/sublimetext-filehistory>
        """
        if to_stamp is None:
            to_stamp = time()
        rem = to_stamp - from_stamp

        def divide(rem, mod):
            return rem % mod, int(rem // mod)

        def subtract(rem, div):
            n = int(rem // div)
            return n,  rem - n * div

        seconds, rem = divide(rem, 60)
        minutes, rem = divide(rem, 60)
        hours, days = divide(rem, 24)
        years, days = subtract(days, 365)
        months, days = subtract(days, 30)
        weeks, days = subtract(days, 7)

        magnitudes = []
        first = None
        values = locals()
        for i, magnitude in enumerate(('years', 'months', 'weeks', 'days', 'hours', 'minutes', 'seconds')):
            v = int(values[magnitude])
            if v == 0:
                continue
            s = '{} {}'.format(v, magnitude)
            if v == 1:  # strip plural s
                s = s[:-1]
            # handle precision limit
            if first is None:
                first = i
            elif first + precision <= i:
                break
            magnitudes.append(s)

        age = ', '.join(magnitudes)
        return (age or '0 seconds') + ' ago'


class RequesterStageRequestFromHistoryCommand(RequesterCommand):
    """Stage request chosen from requester history in context of env under
    which request was originally executed.
    """
    def run(self, edit, request, env_string, file, env_file, **kwargs):
        """Client must pass `request` and env parameters.
        """
        self.FROM_HISTORY = True
        self.request = request
        self.view.settings().set('requester.env_string', env_string)
        self.view.settings().set('requester.file', file)
        self.view.settings().set('requester.env_file', env_file)
        RequestCommandMixin.run(self, edit)

    def get_requests(self):
        return [self.request]

    def reset_env_string(self):
        pass

    def reset_file(self):
        pass

    def reset_env_file(self):
        pass


class RequesterNavigateRequestHistoryCommand(sublime_plugin.TextCommand):
    """`TextCommand` to cycle through and stage previously executed requests. Can
    only be executed from response view. Replaces text in view with request string
    and response metadata.
    """
    def run(self, edit, back):
        from .request import response_tab_bindings
        view = self.view
        if not view.settings().get('requester.response_view', False):
            return
        reqs = view.settings().get('requester.request_history', [])
        index = view.settings().get('requester.request_history_index', len(reqs)-1)

        if back:
            index -= 1
        else:
            index += 1
        if index < 0 or index >= len(reqs):
            return

        try:
            req = reqs[index]
        except IndexError as e:
            sublime.error_message('NavigateLocal Error: {}'.format(e))
            return
        view.settings().set('requester.request_history_index', index)

        view.run_command('requester_replace_view_text',
                         {'text': '{}\n\n{}\n'.format(req, response_tab_bindings()), 'point': 0})
