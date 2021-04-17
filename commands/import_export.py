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
from urllib.parse import urlencode, parse_qsl

from ..deps.requests import Request

from .request import RequesterCommand
from ..core.responses import prepare_request
from ..core.helpers import is_instance


PreparedRequest = namedtuple('PreparedRequest', 'request, args, kwargs, session')


class RequestAcceptsAllArgs(Request):
    """Ensures that invalid args and kwargs are not passed to `requests.Request`.
    """
    def __init__(self, method=None, url=None, headers=None, files=None, data=None, params=None,
                 auth=None, cookies=None, hooks=None, json=None, *args, **kwargs):
        super().__init__(method, url, headers, files, data, params, auth, cookies, hooks, json)


class ArgumentParserErrorRaisesException(argparse.ArgumentParser):
    def error(self, message):
        """This ensures `sys.exit` isn't called if there's a parsing error,
        because this causes Sublime Text to hang indefinitely.
        """
        raise Exception(str(message))


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
                RequestAcceptsAllArgs(*req.args, **req.kwargs), args, kwargs, req.session
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
    """Export selected requester requests to equivalent HTTPie requests.
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
                request = curl_to_request(curl)
            except Exception as e:
                sublime.error_message('Conversion Error: {}'.format(e))
                traceback.print_exc()
            else:
                requests.append(request)

        if not requests:
            return

        header = '# import from cURL'
        view = self.view.window().new_file()
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n\n' + '\n\n\n'.join(requests) + '\n', 'point': 0})
        view.set_syntax_file('Packages/Requester/syntax/requester-source.sublime-syntax')
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
    property on a response instance, which means requests don't have to be sent
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

    auth_string = ''
    auth = kwargs.get('auth', None)
    if isinstance(auth, tuple):
        auth_string = " -u '{}:{}'".format(auth[0], auth[1])
    elif is_instance(auth, 'HTTPBasicAuth'):
        auth_string = " -u '{}:{}'".format(auth.username, auth.password)

    return "curl -X {method}{auth}{headers}{cookies}{data} '{url}{qs}'".format(
        method=req.method,
        auth=auth_string,
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
        elif is_instance(auth, 'HTTPBasicAuth'):
            auth_string = ' -a {}:{}'.format(auth.username, auth.password)
        elif is_instance(auth, 'HTTPDigestAuth'):
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
    """Lifted from: https://github.com/spulec/uncurl, but with some improvements.

    Rewritten to remove `six` and `xerox` dependencies, and add parsing of cookies
    passed in `-b` or `--cookies` named argument Also added support for `-A` and
    `-G` args. Removed various bugs.
    """
    curl = curl.replace('\\\n', '').replace('\\', '')
    if not hasattr(sys, 'argv'):
        sys.argv = ['']

    parser = ArgumentParserErrorRaisesException()
    parser.add_argument('command')
    parser.add_argument('url')
    parser.add_argument('-X', '--request', default=None)
    parser.add_argument('-d', '--data', default=None)
    parser.add_argument('-G', '--get', action='store_true', default=False)
    parser.add_argument('-b', '--cookie', default=None)
    parser.add_argument('-H', '--header', action='append', default=[])
    parser.add_argument('-A', '--user-agent', default=None)
    parser.add_argument('--data-binary', default=None)
    parser.add_argument('--data-raw', default=None)
    parser.add_argument('--compressed', action='store_true')

    tokens = shlex.split(curl, comments=True)
    parsed_args, _ = parser.parse_known_args(tokens)

    method = 'get'
    if parsed_args.request:
        method = parsed_args.request

    base_indent = ' ' * 4
    post_data = parsed_args.data or parsed_args.data_binary or parsed_args.data_raw or ''
    if post_data:
        if not parsed_args.request:
            method = 'post'
        try:
            post_data = json.loads(post_data)
        except ValueError:
            try:
                post_data = dict(parse_qsl(post_data))
            except:
                pass

    cookies_dict = {}

    if parsed_args.cookie:
        cookies = parsed_args.cookie.split(';')
        for cookie in cookies:
            key, value = cookie.strip().split('=')
            cookies_dict[key] = value

    data_arg = 'data'
    headers_dict = {}
    for header in parsed_args.header:
        key, value = header.split(':', 1)
        if key.lower().strip() == 'content-type' and value.lower().strip() == 'application/json':
            data_arg = 'json'

        if key.lower() == 'cookie':
            cookies = value.split(';')
            for cookie in cookies:
                key, value = cookie.strip().split('=', 1)
                cookies_dict[key] = value
        else:
            headers_dict[key] = value.strip()
    if parsed_args.user_agent:
        headers_dict['User-Agent'] = parsed_args.user_agent

    qs = ''
    if parsed_args.get:
        method = 'get'
        try:
            qs = '?{}'.format(urlencode(post_data))
        except:
            qs = '?{}'.format(str(post_data))
        post_data = {}

    result = """requests.{method}('{url}{qs}',{data}\n{headers},\n{cookies},\n)""".format(
        method=method.lower(),
        url=parsed_args.url,
        qs=qs,
        data='\n{}{}={},'.format(base_indent, data_arg, post_data) if post_data else '',
        headers='{}headers={}'.format(base_indent, headers_dict),
        cookies='{}cookies={}'.format(base_indent, cookies_dict),
    )
    return result
