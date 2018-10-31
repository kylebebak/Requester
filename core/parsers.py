import re
from collections import namedtuple

from .helpers import prepend_scheme


VERBS = '(get|options|head|post|put|patch|delete)\('
PREFIX = '[\w_][\w\d_]*\.'
PREFIX_VERBS = PREFIX + VERBS
ASSERTIONS = 'assert \{'

Selection = namedtuple('Selection', 'selection, ordering')
TypedSelection = namedtuple('TypedSelection', 'selection, type')
RequestAssertion = namedtuple('RequestAssertion', 'request, assertion')


def parse_requests(s, **kwargs):
    """Parse string for all calls to `{name}.{verb}(`, or simply `{verb}(`.

    Returns a list of request strings.
    """
    selections = parse(s, '(', ')', [PREFIX_VERBS, VERBS], **kwargs)
    return [sel.selection for sel in selections]


def parse_tests(s):
    """Parse string and return an ordered list of (request, assertion) strings.
    """
    requests = [TypedSelection(sel, 'request') for sel in parse(s, '(', ')', [PREFIX_VERBS, VERBS])]
    assertions = [TypedSelection(sel, 'assertion') for sel in parse(s, '{', '}', [ASSERTIONS])]
    selections = requests + assertions
    selections.sort(key=lambda s: s.selection.ordering)

    tests = []
    for i, s in enumerate(selections):
        try:
            next_s = selections[i+1]
        except IndexError:
            break
        else:
            if s.type == 'request' and next_s.type == 'assertion':
                tests.append(RequestAssertion(s.selection.selection, next_s.selection.selection))
    return tests


def parse(s, open_bracket, close_bracket, match_patterns, n=None, es=None):
    """Parse string `s` for selections that begin with at least one of the
    specified match patterns. Continue expanding each selection until its opening
    and closing brackets are balanced.

    Returns a list of `Selection` instances. Optionally stop after `n` selections
    have been parsed.

    Also supports a shorthand syntax for basic, one-line GET requests.
    """
    start_indices = []

    index = 0
    lines = s.splitlines(True)
    for line in lines:
        if n and len(start_indices) >= n:
            break
        for pattern in match_patterns:
            # for multiline requests, match must occur at start of line,
            # to diminish risk of matching something like 'get(' in the middle of a string
            if re.match(pattern, line):
                start_indices.append(index)
                break
        index += len(line)

    if not start_indices and len(lines) == 1:  # shorthand syntax for basic, one-line GET requests
        # if selection has only one line, we can safely search for start index of first match,
        # even if it's not at start of line
        match = re.search(pattern, line)
        if not match:
            return [Selection("get('{}')".format(prepend_scheme(s.strip().strip('"').strip("'"))), 0)]
        start_indices.append(match.start())
    if es:  # replace selection with extended selection AFTER `start_indices` have been found
        s = es

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
