import sublime

import re
from collections import namedtuple


VERBS = '(get|options|head|post|put|patch|delete)\('
PREFIX = '[\w_][\w\d_]*\.'
PREFIX_VERBS = PREFIX + VERBS
ASSERTIONS = 'assert \{'

Selection = namedtuple('Selection', 'selection, ordering')
TypedSelection = namedtuple('TypedSelection', 'selection, type')
Request = namedtuple('Request', 'request, method, url, args, kwargs, ordering')
RequestAssertion = namedtuple('RequestAssertion', 'request, assertion')


def parse_requests(s, env, n=None):
    """Parse string for all calls to `{name}.{verb}(`, or simply `{verb}(`.

    Returns a list of `Request` instances.
    """
    selections = parse(s, '(', ')', [PREFIX_VERBS, VERBS], n=n)
    return [prepare_request(sel, env) for sel in selections]


def parse_tests(s, env):
    """Parse string and return an ordered list of (request, assertion) test pairs,
    where the first value in each pair is a `Request` instance.
    """
    requests = [TypedSelection(sel, 'request') for sel in parse(s, '(', ')', [PREFIX_VERBS, VERBS])]
    assertions = [TypedSelection(sel, 'assertion') for sel in parse(s, '{', '}', [ASSERTIONS])]
    selections = requests + assertions
    selections.sort(key=lambda s: s.ordering)

    tests = []
    for i in range(len(selections)):
        s = selections[i]
        try:
            next_s = selections[i+1]
        except IndexError:
            break
        else:
            if s.type == 'request' and next_s.type == 'assertion':
                tests.append(RequestAssertion(
                    prepare_request(s.selection, env), next_s.selection.selection
                ))
    return tests


def parse(s, open_bracket, close_bracket, match_patterns, n=None):
    """Parse string `s` for selections that begin with at least one of the
    specified match patterns. Continue expanding each selection until its opening
    and closing brackets are balanced.

    Returns a list of `Selection` instances. Optionally stop after `n` selections
    have been parsed.
    """
    start_indices = []

    index = 0
    for line in s.splitlines(True):
        if n and len(start_indices) >= n:
            break
        for pattern in match_patterns:
            if re.match(pattern, line):
                start_indices.append(index)
                break
        index += len(line)

    sq, dq, comment, escape = False, False, False, False
    end_indices = []
    for index in start_indices:
        if n and len(end_indices) >= n:
            break

        bc = 0  # bracket count
        while True:
            c = s[index]
            if c == '\n':  # new line always terminates comment
                comment = False

            if c == '\\':  # escape char skips next char, unless it's a new line
                escape = True
                index += 1
                continue

            if escape:
                escape = False
                index += 1
                continue

            if c == "'" and not dq and not comment:
                sq = not sq
            if c == '"' and not sq and not comment:
                dq = not dq
            if c == '#' and not sq and not dq:
                comment = True
            if sq or dq or comment:
                index += 1
                continue

            if c == open_bracket:
                bc += 1
            elif c == close_bracket:
                bc -= 1
                if bc == 0:
                    end_indices.append(index)
                    break
            index += 1

    # make sure there are no "unclosed" selections
    assert len(start_indices) == len(end_indices)

    selections = []
    for pair in zip(start_indices, end_indices):
        selections.append(Selection(
            s[pair[0]:pair[1]+1], pair[0]
        ))
    return selections


def parse_args(*args, **kwargs):
    """Used in conjunction with eval to parse args and kwargs from a string.
    """
    return args, kwargs


def prepare_request(selection, env):
    """If request is not prefixed with "{var_name}.", prefix request with
    "requests.", because this module is guaranteed to be in the scope under which
    the request is evaluated. Accepts a `Selection` instance and returns a
    `Request` instance.

    Also, ensure request can time out so it doesn't hang indefinitely.
    http://docs.python-requests.org/en/master/user/advanced/#timeouts
    """
    r, ordering = selection  # unpack namedtuple
    r = r.strip()
    if not re.match(PREFIX, r):
        r = 'requests.' + r

    env['__parse_args__'] = parse_args
    index = r.index('(')
    try:
        args, kwargs = eval('__parse_args__{}'.format(r[index:]), env)
    except:
        args, kwargs = [], {}

    method = r[:index].split('.')[1].strip().upper()
    url = ''
    if 'url' not in kwargs:
        # move url from args to kwargs, easy because url is first arg in all calls to requests
        try:
            url = args[0]
            args = args[1:]  # can't pop from tuple
        except:
            pass  # this method isn't responsible for raising exceptions
        else:
            kwargs['url'] = url

    if 'timeout' not in kwargs:
        settings = sublime.load_settings('Requester.sublime-settings')
        timeout = settings.get('timeout', None)
        kwargs['timeout'] = timeout
        r = r[:-1] + ', timeout={})'.format(timeout)  # put timeout kwarg into request string
    return Request(r, method, url, args, kwargs, ordering)
