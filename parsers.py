import re
from collections import namedtuple


VERBS = '(get|options|head|post|put|patch|delete)\('
PREFIX_VERBS = '[\w_][\w\d_]*\.' + VERBS
ASSERTIONS = 'assert \{'

Selection = namedtuple('Selection', 'selection, start_index, type')
RequestAssertion = namedtuple('RequestAssertion', 'request, assertion')

def parse_requests(s):
    """Parse string for all calls to `{name}.{verb}(`, or simply `{verb}(`.

    Returns a list of strings with calls to the `requests` library.
    """
    selections = parse(s, '(', ')', [PREFIX_VERBS, VERBS])
    return [s.selection for s in selections]


def parse_tests(s):
    """Parse string and return a list of (request, assertion) test pairs.
    """
    requests = parse(s, '(', ')', [PREFIX_VERBS, VERBS], 'request')
    assertions = parse(s, '{', '}', [ASSERTIONS], 'assertion')
    selections = requests + assertions
    selections.sort(key=lambda s: s.start_index)

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


def parse(s, open_bracket, close_bracket, match_patterns, type_=''):
    """Parse string for selections that begin with at least one of the specified
    match patterns. Continue expanding each selection until its opening and
    closing brackets are balanced.

    Chokes on inline comments if they contain unbalanced brackets. Clients should
    catch any exception raised by this method and handle it as a parsing error.
    """
    start_indices = []

    index = 0
    for line in s.splitlines(True):
        for pattern in match_patterns:
            if re.match(pattern, line):
                start_indices.append(index)
                break
        index += len(line)

    end_indices = []
    for index in start_indices:
        bc = 0 # bracket count
        while True:
            if s[index] == open_bracket:
                bc += 1
            elif s[index] == close_bracket:
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
