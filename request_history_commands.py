import sublime, sublime_plugin

import os
import json
from time import time
from collections import OrderedDict

from .request_commands import RequesterCommand
from .core import RequestCommandMixin


class RequesterHistoryCommand(sublime_plugin.WindowCommand):
    """Loads request history from file, and populates quick panel with list of requests in reverse chronological order. If a request is chosen from quick panel, invoke
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
        self.requests = list( reversed(list(rh.items())) )

        self.window.show_quick_panel(
            [self.get_entry_parts(r) for r in self.requests],
            self.on_done
        )

    def get_entry_parts(self, r):
        """Display request and other properties for each entry.
        """
        return [
            self.remove_prefix(r[0]),
            '{}: {}'.format( self.approximate_age(r[1]['ts']), r[1]['code'] ),
            r[1]['url'].split('?')[0],
            r[1]['file'] or '?',
        ]

    def on_done(self, index):
        """Callback for quick panel choice.
        """
        if index < 0: # e.g. user presses escape
            return

        request = self.requests[index]
        params_dict = request[1]
        params_dict['request'] = request[0]
        self.window.run_command('requester_replay_request_from_history', params_dict)

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
            if v == 1: # strip plural s
                s = s[:-1]
            # handle precision limit
            if first is None:
                first = i
            elif first + precision <= i:
                break
            magnitudes.append(s)

        return ', '.join(magnitudes) + ' ago'


class RequesterReplayRequestFromHistoryCommand(RequesterCommand):
    """
    """
    def run(self, edit, request, env_string, file, env_file, **kwargs):
        """Specify `request` and env parameters.
        """
        self.PREPARE_REQUESTS = False
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
