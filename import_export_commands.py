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
from collections import namedtuple
from requests import Request
from urllib.parse import urlencode

from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from .core.responses import prepare_request
from .request_commands import RequesterCommand


PreparedRequest = namedtuple('PreparedRequest', 'request, args, kwargs, session')


def get_exports(requests, env, exporter):
    """Takes list of request strings and prepares them in context of `env`, then
    converts them to list of requests in a new syntax using `exporter` function.
    """
    errors = []
    prepared_requests = []
    for i, request in enumerate(requests):
        req = prepare_request(request, env, i)

        args = req.args.copy()
        kwargs = req.kwargs.copy()
        req.kwargs.pop('timeout', None)
        req.kwargs.pop('filename', None)

        # not pretty, but it makes sure calls to requests.(get|post|put|patch)
        # match up with `requests.Request` method signature
        if req.method == 'GET':
            if len(req.args) == 2:
                req.kwargs['params'] = req.args.pop()
        if req.method in ('PUT', 'PATCH'):
            if len(req.args) == 2:
                req.kwargs['data'] = req.args.pop()
        if req.method in ('POST'):
            if len(req.args) == 3:
                req.kwargs['json'] = req.args.pop()
            if len(req.args) == 2:
                req.kwargs['data'] = req.args.pop()
        req.args.insert(0, req.method)

        try:
            prepared_requests.append(PreparedRequest(
                Request(*req.args, **req.kwargs), args, kwargs, req.session
            ))
        except Exception as e:
            errors.append(str(e))
            traceback.print_exc()

    exports = []
    for request in prepared_requests:
        try:
            exports.append(exporter(request))
        except Exception as e:
            errors.append(str(e))
            traceback.print_exc()

    if errors:
        sublime.error_message('\n\n'.join(errors))
    return exports


class RequesterExportToCurlCommand(RequesterCommand):
    """Export selected requester requests to equivalent cURL requests.
    """
    def make_requests(self, requests, env):
        exports = get_exports(requests, env, request_to_curl)
        if not exports:
            return

        date = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        header = '# export to cURL\n# {}'.format(date)

        view = self.view.window().new_file()
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n\n' + '\n\n\n'.join(exports) + '\n', 'point': 0})
        view.set_syntax_file('Packages/ShellScript/Shell-Unix-Generic.sublime-syntax')
        view.set_name('cURL')
        view.set_scratch(True)

    def handle_response(self, response):
        return


class RequesterExportToHttpieCommand(RequesterCommand):
    """Export selected requester requests to equivalent cURL requests.
    """
    def make_requests(self, requests, env):
        exports = get_exports(requests, env, request_to_httpie)
        if not exports:
            return

        date = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        header = '# export to HTTPie\n# {}'.format(date)

        view = self.view.window().new_file()
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n\n' + '\n\n\n'.join(exports) + '\n', 'point': 0})
        view.set_syntax_file('Packages/ShellScript/Shell-Unix-Generic.sublime-syntax')
        view.set_name('HTTPie')
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

    Modified to accept a prepared request instance, instead of the `request`
    property on a response intance, which means requests don't have to be sent
    before converting them to cURL, and also extraneous headers aren't added.
    """
    req, args, kwargs, session = request

    data = ''
    if req.data:
        data = urlencode(req.data)
    elif req.json:
        data = json.dumps(req.json)
        req.headers['Content-Type'] = 'application/json'

    cookies = ''
    if req.cookies:
        cookies = ['{}={}'.format(k, v) for k, v in req.cookies.items()]
        cookies = ';'.join(sorted(cookies))

    headers = ["'{}: {}'".format(k, v) for k, v in req.headers.items()]
    headers = " -H ".join(sorted(headers))

    return "curl -X {method}{headers}{cookies}{data} '{url}{qs}'".format(
        method=req.method,
        headers=' -H {}'.format(headers) if headers else '',
        cookies=" -b '{}'".format(cookies) if cookies else '',
        data=" -d '{}'".format(data) if data else '',
        url=req.url,
        qs='?{}'.format(urlencode(req.params)) if req.params else '',
    )


def request_to_httpie(request):
    """Converts prepared request instance to a string that calls HTTPie.
    """
    req, args, kwargs, session = request

    cookies = ''
    if req.cookies:
        cookies = ['{}={}'.format(k, v) for k, v in req.cookies.items()]
        cookies = " 'Cookie:{}'".format(
            ';'.join(sorted(cookies))
        )

    headers = ''
    if req.headers:
        headers = ['{}:{}'.format(k, v) for k, v in req.headers.items()]
        headers = ' {}'.format(' '.join(headers))

    method = req.method.upper()
    timeout = kwargs.get('timeout', None)
    filename = kwargs.get('filename', None)

    auth_string = ''
    auth = kwargs.get('auth', None)
    if auth:
        if isinstance(auth, tuple):
            auth_string = ' -a {}:{}'.format(auth[0], auth[1])
        elif isinstance(auth, HTTPBasicAuth):
            auth_string = ' -a {}:{}'.format(auth.username, auth.password)
        elif isinstance(auth, HTTPDigestAuth):
            auth_string = ' -A digest -a {}:{}'.format(auth.username, auth.password)

    qs = ''
    for k, v in req.params.items():
        qs += " {}=='{}'".format(k, v)

    data = ''
    form = ''
    stdin = ''
    if req.data:
        data = ["{}='{}'".format(k, v) for k, v in req.data.items()]
        data = ' {}'.format(' '.join(data))
        form = ' -f'
    elif req.json:
        if isinstance(req.json, dict):
            for k, v in req.json.items():
                if isinstance(v, str):
                    data += ' {}={}'.format(k, v)
                elif isinstance(v, (list, dict)):
                    data += " {}:='{}'".format(k, json.dumps(v))
                else:  # boolean, number
                    data += ' {}:={}'.format(k, str(v).lower())
        else:
            stdin = "echo '{}' | ".format(json.dumps(req.json))

    return '{stdin}http{session}{form}{auth}{timeout}{method} {url}{qs}{headers}{cookies}{data}{filename}'.format(
        stdin=stdin,
        session=' --session={}'.format(session) if session else '',
        form=form,
        auth=auth_string,
        timeout=' --timeout={}'.format(timeout) if timeout else '',
        method=' {}'.format(method) if method != 'GET' else '',
        url=req.url,
        qs=qs,
        headers=headers,
        cookies=cookies,
        data=data,
        filename=' > {}'.format(filename) if filename else '',
    )


def curl_to_request(curl):
    """Lifted from: https://github.com/spulec/uncurl

    Rewritten slightly to remove `six` and `xerox` dependencies, and add parsing
    of cookies passed in `-b` or `--cookies` named argument. Also removed some
    bugs.
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
    parser.add_argument('-A', '--user-agent', default=None)
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
            post_data = post_data_json
        else:
            post_data = "'{}'".format(post_data)

        data_token = '{}data={},\n'.format(base_indent, post_data)

    cookie_dict = {}

    if parsed_args.cookie:
        cookies = parsed_args.cookie.split(';')
        for cookie in cookies:
            key, value = cookie.strip().split('=')
            cookie_dict[key] = value

    quoted_headers = {}
    for header in parsed_args.header:
        key, value = header.split(':', 1)

        if key.lower() == 'cookie':
            cookies = value.split(';')
            for cookie in cookies:
                key, value = cookie.strip().split('=')
                cookie_dict[key] = value
        else:
            quoted_headers[key] = value.strip()
    if parsed_args.user_agent:
        quoted_headers['User-Agent'] = parsed_args.user_agent

    result = """requests.{method}('{url}',\n{data_token}{headers_token},\n{cookies_token},\n)""".format(
        method=method.lower(),
        url=parsed_args.url,
        data_token=data_token,
        headers_token='{}headers={}'.format(base_indent, quoted_headers),
        cookies_token='{}cookies={}'.format(base_indent, cookie_dict),
    )
    return result
