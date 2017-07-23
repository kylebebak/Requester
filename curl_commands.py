import sublime
import sublime_plugin

import datetime
import argparse
import json
import shlex
import re
import sys
import traceback
from time import time
from collections import OrderedDict
from requests import Request
from urllib.parse import urlencode

from .core.responses import prepare_request
from .request_commands import RequesterCommand


class RequesterExportToCurlCommand(RequesterCommand):
    """Export selected requester requests to equivalent cURL requests.
    """
    def make_requests(self, requests, env):
        errors = []
        prepared_requests = []
        for i, request in enumerate(requests):
            r = prepare_request(request, env, i)
            r.args.insert(0, r.method)
            r.kwargs.pop('timeout')
            try:
                prepared_requests.append(Request(*r.args, **r.kwargs))
            except Exception as e:
                errors.append(str(e))
                traceback.print_exc()

        curls = []
        for request in prepared_requests:
            try:
                curls.append(request_to_curl(request))
            except Exception as e:
                errors.append(str(e))
                traceback.print_exc()

        if errors:
            sublime.error_message('\n\n'.join(errors))
        if not curls:
            return

        date = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        header = '# export to cURL\n# {}'.format(date)

        view = self.view.window().new_file()
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n\n' + '\n\n\n'.join(curls) + '\n', 'point': 0})
        view.set_syntax_file('Packages/ShellScript/Shell-Unix-Generic.sublime-syntax')
        view.set_name('cURL')
        view.set_scratch(True)

    def handle_response(self, response):
        return


class RequesterImportFromCurlCommand(sublime_plugin.TextCommand):
    """Import cURL requests to Python requests.
    """
    def run(self, edit):
        curls = self.get_curls()
        requests = []
        for curl in curls:
            try:
                requests.append(curl_to_request(curl))
            except Exception as e:
                sublime.error_message('Conversion Error: {}'.format(e))
                traceback.print_exc()

        if not requests:
            return

        header = '# import from cURL'
        view = self.view.window().new_file()
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n\n' + '\n\n\n'.join(requests) + '\n', 'point': 0})
        view.set_syntax_file('Packages/Python/Python.sublime-syntax')
        view.set_name('requests')
        view.set_scratch(True)

    def get_curls(self):
        """Parses curls from multiple selections. If nothing is highlighted,
        cursor's current line is taken as selection.
        """
        view = self.view
        curls = []
        for region in view.sel():
            if not region.empty():
                selection = view.substr(region)
            else:
                selection = view.substr(view.line(region))
            try:
                curls_ = self.parse_curls(selection)
            except Exception as e:
                sublime.error_message('Parse Error: {}'.format(e))
                traceback.print_exc()
            else:
                for curl in curls_:
                    curls.append(curl)
        return curls

    @staticmethod
    def parse_curls(s):
        """Rudimentary parser for calls to `curl`. These calls can't be intermixed
        with calls to any other functions, but parser correctly ignores comments.
        """
        curls = []
        curl = None
        for line in s.splitlines(True):
            line = line.split('#')[0]  # remove everything after comment in each line
            if re.match('curl ', line):
                if curl is not None:
                    curls.append(curl)
                curl = ''
            if curl is not None:
                curl += line + '\n'
        curls.append(curl)
        return curls


def request_to_curl(request):
    """Inspired by: https://github.com/oeegor/curlify

    Modified to accept a prepared request instance, intead of the `request`
    property on a response intance, which requests don't have to be sent to
    convert them to cURL, and also extraneous headers aren't added.
    """
    data = ''
    if request.data:
        data = urlencode(request.data)
    elif request.json:
        data = json.dumps(request.json)
        request.headers['Content-Type'] = 'application/json'

    cookies = ''
    if request.cookies:
        cookies = ['{}={}'.format(k, v) for k, v in request.cookies.items()]
        cookies = ';'.join(sorted(cookies))

    headers = ["'{}: {}'".format(k, v) for k, v in request.headers.items()]
    headers = " -H ".join(sorted(headers))

    return "curl -X {method}{headers}{cookies}{data} '{uri}{qs}'".format(
        method=request.method,
        headers=' -H {}'.format(headers) if headers else '',
        cookies=" -b '{}'".format(cookies) if cookies else '',
        data=" -d '{}'".format(data) if data else '',
        uri=request.url,
        qs='?{}'.format(urlencode(request.params)) if request.params else '',
    )


def curl_to_request(curl):
    """Lifted from: https://github.com/spulec/uncurl

    Rewritten slightly to remove `six` and `xerox` dependencies, and add parsing
    of cookies passed in `-b` or `--cookies` named argument.
    """
    curl = curl.replace('\\\n', '').replace('\\', '')
    sys.argv = ['__requester__']
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    parser.add_argument('url')
    parser.add_argument('-X', '--request', default=None)
    parser.add_argument('-d', '--data')
    parser.add_argument('-b', '--cookie', default=None)
    parser.add_argument('-H', '--header', action='append', default=[])
    parser.add_argument('--data-binary', default=None)
    parser.add_argument('--compressed', action='store_true')

    tokens = shlex.split(curl)
    parsed_args = parser.parse_args(tokens)

    method = 'get'
    if parsed_args.request:
        method = parsed_args.request

    base_indent = ' ' * 4
    data_token = ''
    post_data = parsed_args.data or parsed_args.data_binary
    if post_data:
        if not parsed_args.request:
            method = 'post'
        try:
            post_data_json = json.loads(post_data)
        except ValueError:
            post_data_json = None

        # if we found JSON and it's a dict, pull it apart; otherwise, leave it as a string
        if post_data_json and isinstance(post_data_json, dict):
            post_data = dict_to_pretty_string(post_data_json)
        else:
            post_data = "'{}'".format(post_data)

        data_token = '{}data={},\n'.format(base_indent, post_data)

    cookie_dict = OrderedDict()

    if parsed_args.cookie:
        cookies = parsed_args.cookie.split(';')
        for cookie in cookies:
            key, value = cookie.strip().split('=')
            cookie_dict[key] = value

    quoted_headers = OrderedDict()
    for header in parsed_args.header:
        key, value = header.split(':', 1)

        if key.lower() == 'cookie':
            cookies = value.split(';')
            for cookie in cookies:
                key, value = cookie.strip().split('=')
                cookie_dict[key] = value
        else:
            quoted_headers[key] = value.strip()

    result = """requests.{method}('{url}',\n{data_token}{headers_token},\n{cookies_token},\n)""".format(
        method=method.lower(),
        url=parsed_args.url,
        data_token=data_token,
        headers_token='{}headers={}'.format(base_indent, dict_to_pretty_string(quoted_headers)),
        cookies_token='{}cookies={}'.format(base_indent, dict_to_pretty_string(cookie_dict)),
    )
    return result


def dict_to_pretty_string(the_dict, indent=4):
    if not the_dict:
        return '{}'

    return ('\n' + ' ' * indent).join(
        json.dumps(the_dict, sort_keys=True, indent=indent, separators=(',', ': ')).splitlines()
    )
