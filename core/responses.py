import sublime

import re
from urllib import parse
from concurrent import futures
from collections import namedtuple, deque

import requests

from .parsers import PREFIX
from .helpers import truncate, prepend_scheme


Request_ = namedtuple('Request', 'request, method, url, args, kwargs, ordering, session, skwargs, error')
Response = namedtuple('Response', 'req, res, err')

methods = {
    'GET': requests.get,
    'OPTIONS': requests.options,
    'HEAD': requests.head,
    'POST': requests.post,
    'PUT': requests.put,
    'PATCH': requests.patch,
    'DELETE': requests.delete,
}


class Request(Request_):
    """Hashable `Request` namedtuple.
    """
    def __hash__(self):
        return hash(self.ordering)

    def __eq__(self, other):
        return self.ordering == other.ordering

    def __ne__(self, other):
        return not(self == other)


def parse_args(*args, **kwargs):
    """Used in conjunction with eval to parse args and kwargs from a string.
    """
    return args, kwargs


class ResponseThreadPool:
    """Allows requests to be invoked concurrently, and allows client code to
    inspect instance's responses as they are returned.
    """
    def get_response(self, request, ordering):
        """Calls request with specified args and kwargs parsed from request
        string.

        Also sets "Response" key in env to `Response` object, to provide true
        "chaining" of requests. If two requests are run serially, the second
        request can reference the response returned by the previous request.
        """
        if isinstance(request, Request):  # no need to prepare request
            req = request._replace(ordering=ordering)
        else:
            req = prepare_request(request, self.env, ordering)
        if req.error is not None:
            return Response(req, None, None)

        if self.handle_special(req):
            return Response(req, None, 'skwarg')  # "special" requests handled separately
        self.pending_requests.add(req)
        res, err = None, ''
        if self.is_done:  # prevents further requests from being made if pool is cancelled
            return Response(req, res, err)  # check using: https://requestb.in/

        try:
            if req.session:
                session = self.env.get(req.session)
                if isinstance(session, requests.sessions.Session):
                    res = getattr(session, req.method.lower())(*req.args, **req.kwargs)
                else:
                    err = 'Session Error: there is no session `{}` defined in your environment'.format(req.session)
            else:
                res = methods.get(req.method)(*req.args, **req.kwargs)
        except requests.Timeout:
            err = 'Timeout Error: the request timed out'
        except requests.ConnectionError:
            err = 'Connection Error: check your connection'
        except SyntaxError as e:
            err = '{}: {}\n\n{}'.format('Syntax Error', e,
                                        'Run "Requester: Show Syntax" to review properly formatted requests')
        except TypeError as e:
            err = '{}: {}'.format('Type Error', e)
        except Exception as e:
            err = '{}: {}'.format('Other Error', e)

        self.env['Response'] = res  # to allow "chaining" of serially executed requests
        if req.skwargs.get('name'):
            try:
                self.env[str(req.skwargs.get('name'))] = res  # calling str could raise exception...
            except Exception as e:
                print('Name Error: {}'.format(e))
        return Response(req, res, err)

    def handle_special(self, req):
        """Handle "special" requests, such as downloads and uploads.
        """
        from ..commands.download import Download
        from ..commands.upload import Upload
        if 'filename' in req.skwargs:
            Download(req, req.skwargs['filename'])
            return True
        if 'streamed' in req.skwargs:
            Upload(req, req.skwargs['streamed'], 'streamed')
            return True
        if 'chunked' in req.skwargs:
            Upload(req, req.skwargs['chunked'], 'chunked')
            return True
        return False

    def __init__(self, requests, env, max_workers):
        self.is_done = False
        self.responses = deque()
        self.requests = requests
        self.pending_requests = set()
        self.env = env
        self.max_workers = max_workers

    def get_pending_requests(self):
        """Getter for `self.pending_requests`. This is a `set` that's shared
        between threads, which makes iterating over it unsafe.
        """
        return self.pending_requests.copy()

    def run(self):
        """Concurrently invoke `get_response` for all of instance's `requests`.
        """
        with futures.ThreadPoolExecutor(
            max_workers=min(self.max_workers, len(self.requests))
        ) as executor:
            to_do = []
            for i, request in enumerate(self.requests):
                future = executor.submit(self.get_response, request, i)
                to_do.append(future)

            for future in futures.as_completed(to_do):
                result = future.result()
                # `responses` and `pending_requests` are instance properties, which means
                # client code can inspect instance to read responses as they are completed
                if result.req.error is not None or result.err == 'skwarg':
                    continue
                try:
                    self.pending_requests.remove(result.req)
                except KeyError:
                    print('{} was not in pending requests, this is weird...'.format(result.req))
                self.responses.append(result)
        self.is_done = True


def prepare_request(request, env, ordering):
    """Parse and evaluate args and kwargs in request string under context of
    env.

    Also, prepare request string: if request is not prefixed with "{var_name}.",
    prefix request with "requests." Accepts a request string and returns a
    `Request` instance.

    Finally, ensure request can time out so it doesn't hang indefinitely.
    http://docs.python-requests.org/en/master/user/advanced/#timeouts
    """
    settings = sublime.load_settings('Requester.sublime-settings')
    req = prepend_library(request)

    session = None
    if not req.startswith('requests.'):
        session = req.split('.')[0]

    index = req.index('(')
    method = req[:index].split('.')[1].strip().upper()

    env['__parse_args__'] = parse_args
    try:
        args, kwargs = eval('__parse_args__{}'.format(req[index:]), env)
    except Exception as e:
        sublime.error_message('PrepareRequest Error: {}\n{}'.format(
            e, truncate(req, 150)
        ))
        return Request(req, method, None, [], {}, ordering, session, {}, error=str(e))
    else:
        args = list(args)

    url_from_kwargs = True
    url = kwargs.get('url', None)
    if url is None:
        url_from_kwargs = False
        try:
            url = args[0]
        except Exception as e:
            sublime.error_message('PrepareRequest Error: {}\n{}'.format(
                e, truncate(req, 150)
            ))
            return Request(req, method, url, args, kwargs, ordering, session, {}, error=str(e))

    if 'explore' in kwargs:
        req, e_url = kwargs.pop('explore')
        req = replace_method(prepend_library(req), 'get')
        if not same_domain(prepend_scheme(e_url), prepend_scheme(url)):
            # if explore URL does't have same domain as URL, remove auth kwargs from req
            kwargs.pop('params', None)
            kwargs.pop('headers', None)
            kwargs.pop('cookies', None)
            kwargs.pop('auth', None)
            req = replace_url(req, e_url, replace_all=True)
        else:
            req = replace_url(req, e_url, replace_all=False)
        url = prepend_scheme(e_url)
        method = 'GET'
    else:
        url = prepend_scheme(url)

    if url_from_kwargs:
        kwargs['url'] = url
    else:
        args[0] = url

    error = None
    fmt = kwargs.pop('fmt', settings.get('fmt', None))
    name = kwargs.pop('name', None)  # cache response to "chain" requests
    skwargs = {'fmt': fmt, 'name': name}
    if 'filename' in kwargs:
        skwargs['filename'] = str(kwargs.pop('filename'))
    if 'streamed' in kwargs:
        skwargs['streamed'] = str(kwargs.pop('streamed'))
    if 'chunked' in kwargs:
        skwargs['chunked'] = str(kwargs.pop('chunked'))

    if fmt not in ('raw', 'indent', 'indent_sort'):
        error = 'invalid `fmt`, must be one of ("raw", "indent", "indent_sort")'
        sublime.error_message('PrepareRequest Error: {}\n{}'.format(error, truncate(req, 150)))
    if 'timeout' not in kwargs:
        kwargs['timeout'] = settings.get('timeout', None)
    if 'allow_redirects' not in kwargs:
        kwargs['allow_redirects'] = settings.get('allow_redirects', True)
    return Request(req, method, url, args, kwargs, ordering, session, skwargs, error)


def prepend_library(req):
    """Makes sure "requests." is prepended to call to requests.
    """
    req = req.strip()
    if not re.match(PREFIX, req):
        return 'requests.' + req
    return req


def same_domain(e_url, url):
    """Do these URLs have the same domain?

    Note, this method is NOT correct for URLs whose gTLD/ccTLD has one or more '.'
    chars, like "co.uk". See here: https://github.com/john-kurkowski/tldextract

    It is also incorrect for subdomains with more than one segment, although I
    haven't seen URLs like this in production.

    https://raw.githubusercontent.com/toddmotto/public-apis/master/json/entries.json
    This list suggests that public APIs overwhelmingly have gTLDs without '.' chars.
    """
    e_netloc, netloc = parse.urlparse(e_url).netloc, parse.urlparse(url).netloc
    d, dd = sorted([n.split('.') for n in (e_netloc, netloc)], key=lambda d: len(d))
    parts = max(2, len(dd)-1)
    if len(d) < 2:  # not a valid URL, but this method not responsible for raising exception
        return False
    if len(d) < len(dd) - 1:
        return False
    if len(d) == len(dd) - 1:
        dd = dd[1:]  # only compare URL domains, not subdomains
    return d[-parts:] == dd[-parts:]


def replace_method(req, method):
    """Replace method in request string.
    """
    call, args = req.split('(', 1)
    request, _method = call.split('.', 1)
    return '{}.{}({}'.format(request, method, args)


def replace_url(req, url, replace_all):
    """Tries to replace `url` in `req` string. This can fail if user has
    unconventional argument ordering. This is only for exploratory requests.
    """
    call, args = req.split('(', 1)
    if ',' not in req or replace_all:
        return '{}({})'.format(call, repr(url))
    _first, rest = args.split(',', 1)
    return '{}({},{}'.format(call, repr(url), rest)
