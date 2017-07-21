import argparse
import json
import shlex
from collections import OrderedDict


def request_to_curl(request):
    """Lifted entirely from: https://github.com/oeegor/curlify

    Adding pip dependencies in Sublime isn't trivial, and adding a dependency for
    10 line function would be a little silly.
    """
    headers = ["'{0}: {1}'".format(k, v) for k, v in request.headers.items()]
    headers = " -H ".join(sorted(headers))

    return "curl -X {method} -H {headers} -d '{data}' '{uri}'".format(
        data=request.body or '',
        headers=headers,
        method=request.method,
        uri=request.url,
    )


def curl_to_request(curl):
    """Lifted from: https://github.com/spulec/uncurl

    Rewritten slightly to remove `six` and `xerox` dependencies.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    parser.add_argument('url')
    parser.add_argument('-d', '--data')
    parser.add_argument('-b', '--data-binary', default=None)
    parser.add_argument('-H', '--header', action='append', default=[])
    parser.add_argument('--compressed', action='store_true')

    method = 'get'

    tokens = shlex.split(curl)
    parsed_args = parser.parse_args(tokens)

    base_indent = ' ' * 4
    data_token = ''
    post_data = parsed_args.data or parsed_args.data_binary
    if post_data:
        method = 'post'
        try:
            post_data_json = json.loads(post_data)
        except ValueError:
            post_data_json = None

        # If we found JSON and it is a dict, pull it apart. Otherwise, just leave as a string
        if post_data_json and isinstance(post_data_json, dict):
            post_data = dict_to_pretty_string(post_data_json)
        else:
            post_data = "'{}'".format(post_data)

        data_token = '{}data={},\n'.format(base_indent, post_data)

    cookie_dict = OrderedDict()
    quoted_headers = OrderedDict()
    for curl_header in parsed_args.header:
        header_key, header_value = curl_header.split(':', 1)

        if header_key.lower() == 'cookie':
            cookies = header_value.split(';')
            for cookie in cookies:
                key, value = cookie.strip().split('=')
                cookie_dict[key] = value
        else:
            quoted_headers[header_key] = header_value.strip()

    result = """requests.{method}('{url}',
{data_token}{headers_token},
{cookies_token},
)""".format(
        method=method,
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
