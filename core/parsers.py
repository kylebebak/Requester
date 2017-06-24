import re
from collections import namedtuple


VERBS = '(get|options|head|post|put|patch|delete)\('
PREFIX = '[\w_][\w\d_]*\.'
PREFIX_VERBS = PREFIX + VERBS
ASSERTIONS = 'assert \{'

Selection = namedtuple('Selection', 'selection, ordering, type')
RequestAssertion = namedtuple('RequestAssertion', 'request, assertion')


def parse_args(*args, **kwargs):
    """Used in conjunction with eval to parse args and kwargs from a string.
    """
    return args, kwargs


def parse_requests(s, n=None, return_selections=False):
    """Parse string for all calls to `{name}.{verb}(`, or simply `{verb}(`.

    Returns a list of strings with calls to the `requests` library.
    """
    selections = parse(s, '(', ')', [PREFIX_VERBS, VERBS], n=n)
    if return_selections:
        return selections
    return [sel.selection for sel in selections]


def parse_tests(s):
    """Parse string and return an ordered list of (request, assertion) test pairs.
    """
    requests = parse(s, '(', ')', [PREFIX_VERBS, VERBS], 'request')
    assertions = parse(s, '{', '}', [ASSERTIONS], 'assertion')
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
                tests.append(RequestAssertion(s.selection, next_s.selection))
    return tests


def parse(s, open_bracket, close_bracket, match_patterns, type_='', n=None):
    """Parse string for selections that begin with at least one of the specified
    match patterns. Continue expanding each selection until its opening and
    closing brackets are balanced.

    Optionally stop after `n` selections have been parsed.
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

    sq, dq, comment = False, False, False
    end_indices = []
    for index in start_indices:
        if n and len(end_indices) >= n:
            break

        bc = 0 # bracket count
        while True: # fix: this doesn't handle escaped quotes
            c = s[index]

            if c == "'" and not dq and not comment:
                sq = not sq
            if c == '"' and not sq and not comment:
                dq = not dq
            if c == '#' and not comment and not sq and not comment:
                comment = True
            if c == '\n': # new line always terminates comment
                comment = False
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
            s[ pair[0]:pair[1]+1 ], pair[0], type_
        ))
    return selections


def prepare_request(r, timeout):
    """If request is not prefixed with "{var_name}.", prefix request with
    "requests.", because this module is guaranteed to be in the scope under
    which the request is evaluated.

    Also, ensure request can time out so it doesn't hang indefinitely.
    http://docs.python-requests.org/en/master/user/advanced/#timeouts
    """
    r = r.strip()
    if not re.match(PREFIX, r):
        r = 'requests.' + r

    if timeout is not None:
        timeout_string = ', timeout={})'.format(timeout)
        r = r[:-1] + timeout_string
    return r


def truncate(s, l, ellipsis='...'):
    """Truncates string to length `l` if need be and adds `ellipsis`.
    """
    if len(s) > l:
        return s[:l] +  ellipsis
    return s


def clean_url(url):
    """Remove trailing slash and query string from `url`.
    """
    url = url.split('?')[0]
    if url and url[-1] == '/':
        return url[:-1]
    return url
