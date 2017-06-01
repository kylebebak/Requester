import sublime

import re
import json
from collections import namedtuple


Content = namedtuple('Content', 'content, point')
platform = sublime.platform()


def set_response_view_syntax(config, view):
    """Set syntax for `view` based on `content-type` response header.
    """
    if not config.get('highlighting', False):
        return

    view.set_syntax_file('Packages/Requester/requester-response.sublime-syntax')


def get_response_view_content(request, response):
    """Returns a response string that includes metadata, headers and content,
    and the index of the string at which response content begins.
    """
    r = response
    redirects = [res.url for res in r.history] # URLs traversed due to redirects
    redirects.append(r.url) # final URL

    header = '{} {}\n{}s, {}B\n{}'.format(
        r.status_code, r.reason, r.elapsed.total_seconds(), len(r.content),
        ' -> '.join(redirects)
    )
    headers = '\n'.join(
        [ '{}: {}'.format(k, v) for k, v in sorted(r.headers.items()) ]
    )
    try:
        json_dict = r.json()
    except:
        content = r.text
    else: # prettify json regardless of what raw response looks like
        content = json.dumps(json_dict, sort_keys=True, indent=2, separators=(',', ': '))

    replay_binding = '[cmd+r]' if platform == 'osx' else '[ctrl+r]'
    before_content_items = [
        request,
        header,
        '{}: {}'.format('Request Headers', r.request.headers),
        '{} replay request'.format(replay_binding),
        headers
    ]
    cookies = r.cookies.get_dict()
    if cookies:
        before_content_items.insert(3, '{}: {}'.format('Response Cookies', cookies))
    before_content = '\n\n'.join(before_content_items)

    return Content(before_content + '\n\n' + content, len(before_content) + 2)


def prepare_request(r, timeout=None):
    """If request is not prefixed with "{var_name}.", prefix request with
    "requests.", because this module is guaranteed to be in the scope under
    which the request is evaluated.

    Also, ensure request can time out so it doesn't hang indefinitely.
    http://docs.python-requests.org/en/master/user/advanced/#timeouts

    Finally, ensure that request occupies only one line.
    """
    r = r.strip()
    if not re.match('[\w_][\w\d_]*\.', r):
        r = 'requests.' + r

    if timeout is not None:
        timeout_string = ', timeout={})'.format(timeout)
        r = r[:-1] + timeout_string
    return ' '.join(r.split()) # replace all multiple whitespace with single space
