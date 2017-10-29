import sublime
import sublime_plugin

import os
import json
from time import time
from urllib import parse
from collections import OrderedDict

from ..core.helpers import truncate


def load_history(rev=True):
    """Returns list of past requests. Raises exception if history file doesn't
    exist.
    """
    history_file = sublime.load_settings('Requester.sublime-settings').get('history_file', None)
    if not history_file:
        raise KeyError

    history_path = os.path.join(sublime.packages_path(), 'User', history_file)
    with open(history_path, 'r') as f:
        rh = json.loads(f.read() or '{}', object_pairs_hook=OrderedDict)
    requests = list(rh.items())
    if rev:
        requests.reverse()
    return requests


def populate_staging_view(view, index, total,
                          request, method, url, code, ts,
                          meta=None, file=None, env_string=None, env_file=None):
    """Populate staging view with historical request string/metadata.
    """
    from .request import response_tab_bindings, set_save_info_on_view
    view.settings().set('requester.response_view', True)
    view.settings().set('requester.history_view', True)
    view.settings().set('requester.env_string', env_string)
    view.settings().set('requester.file', file)
    view.settings().set('requester.env_file', env_file)
    set_save_info_on_view(view, request)

    config = sublime.load_settings('Requester.sublime-settings')
    max_len = int(config.get('response_tab_name_length', 32))

    meta_parts = [
        '{} {}{}'.format(code, method, ' ({})'.format(meta) if meta else ''),
        url,
        '{}: {}/{}'.format(approximate_age(ts), index+1, total),
        file,
    ]
    meta_string = '\n'.join(s for s in meta_parts if s)
    content = '{}\n\n{}\n\n{}\n'.format(request, response_tab_bindings(), meta_string)
    view.run_command('requester_replace_view_text', {'text': content, 'point': 0})

    path = parse.urlparse(url).path
    if path and path[-1] == '/':
        path = path[:-1]
    view.set_name(truncate('({}) {}: {}'.format(index+1, method, path), max_len))
    view.set_syntax_file('Packages/Requester/syntax/requester-history.sublime-syntax')
    view.set_scratch(True)


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


class RequesterHistoryCommand(sublime_plugin.WindowCommand):
    """Loads request history from file, and populates quick panel with list of
    requests in reverse chronological order. If a request is chosen from quick
    panel, stage request.
    """
    def run(self):
        try:
            self.requests = load_history()
        except Exception as e:
            print(e)
            return

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
                approximate_age(req[1]['ts']),
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

        params_dict = self.requests[index][1]
        total = len(self.requests)
        reversed_index = total - index - 1
        view = self.window.new_file()
        view.settings().set('requester.request_history_index', reversed_index)
        populate_staging_view(view, index, total, **params_dict)


class RequesterPageRequestHistoryCommand(sublime_plugin.TextCommand):
    """`TextCommand` to page through and stage previously executed requests. Can
    only be executed from response view. Replaces text in view with request string
    and response metadata.
    """
    def run(self, edit, back):
        view = self.view
        if not view.settings().get('requester.response_view', False):
            return
        reqs = load_history(rev=False)
        index = view.settings().get('requester.request_history_index', len(reqs)-1)
        total = len(reqs)

        if back:
            index -= 1
        else:
            index += 1
        if index < 0 or index >= len(reqs):
            return

        try:
            params_dict = reqs[index][1]
        except IndexError as e:
            sublime.error_message('RequestHistory Error: {}'.format(e))
            return
        view.settings().set('requester.request_history_index', index)
        populate_staging_view(view, total-index-1, total, **params_dict)
