import sublime
import sublime_plugin

import re
import datetime
from time import time
from urllib import parse
from collections import namedtuple

from .core import RequestCommandMixin
from .core.parsers import parse_tests
from .core.responses import prepare_request


Error = namedtuple('Error', 'prop, expected, got, error')
Result = namedtuple('Result', 'result, assertions, errors')
RequestAssertion = namedtuple('RequestAssertion', 'request, assertion')


class TestParserMixin:
    def get_requests(self):
        """Parses only first highlighted selection.
        """
        view = self.view
        self._tests = []

        for region in view.sel():
            if not region.empty():
                selection = view.substr(region)
            try:
                self._tests = parse_tests(selection)
            except Exception as e:
                sublime.error_message('Parse Error: there may be unbalanced brackets in tests')
                print(e)
            break  # only parse first selection

        return [test.request for test in self._tests]

    def eval_assertion(self, s):
        """Includes `env` that was parsed by `RequestCommandMixin`. Raises an
        exception that should be caught by client code if assertion can't be
        eval'ed or there's anything wrong with assertion.
        """
        dict_string = s.split('assert', 1)[1]
        try:
            assertion = eval(dict_string, self._env)
        except Exception as e:
            raise Exception('{}, {}'.format(dict_string.strip(), e))

        if not isinstance(assertion, dict):
            raise TypeError('assertion {} is not a dictionary'.format(assertion))
        return assertion


class RequesterRunTestsCommand(TestParserMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently. For each request with a
    corresponding assertions dictionary, compare response with assertions and
    display all results in new tab.

    Doesn't work for multiple selections, because absolute order of (request,
    assertion) test pairs is preserved in results tab.
    """
    def run(self, edit, concurrency=10):
        """Allow user to specify concurrency.
        """
        self.MAX_WORKERS = max(1, concurrency)
        super().run(edit)

    def handle_responses(self, responses):
        """Compares response objects with assertions dictionaries and displays a
        test run view that includes all discrepancies.
        """
        if len(self._tests) != len(responses):
            sublime.error_message('Parse Error: something went wrong')
            return

        results, errors = [], []
        count_assertions, count_errors = 0, 0
        for i, response in enumerate(responses):
            try:
                assertion = self.eval_assertion(self._tests[i].assertion)
            except Exception as e:
                errors.append('{}: {}'.format('Assertion Error', e))
            else:
                result = self.get_result(response, assertion)
                count_assertions += result.assertions
                count_errors += result.errors
                results.append(result.result)

        if errors:
            sublime.error_message('\n\n'.join(errors))
        if not results:  # don't open test view if no tests were run
            return

        view = self.view.window().new_file()
        view.set_scratch(True)
        view.settings().set('requester.test_view', True)
        self.set_env_settings_on_view(view)

        header = '-- {} assertion{}, {} error{} --\n'.format(
            count_assertions, '' if count_assertions == 1 else 's',
            count_errors, '' if count_errors == 1 else 's',
        )
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n' + '\n\n'.join(results), 'point': 0})
        view.set_read_only(True)
        view.set_name('Requester Test Run')
        view.set_syntax_file('Packages/Requester/requester-test.sublime-syntax')

    def get_result(self, response, assertion):
        """Get result of comparing response with assertion dict. Ignores keys in
        assertion dict that don't correspond to a valid property or method of
        response.
        """
        req, res, err = response
        result = '{}\nassert {}\n'.format(req.request, assertion)
        errors = []
        count = 0

        assertion = {str(k): v for k, v in assertion.items()}  # make sure keys can be ordered
        for prop, expected in sorted(assertion.items()):
            if prop in ('cookies_schema', 'json_schema', 'headers_schema'):  # jsonschema validation
                count += 1
                from jsonschema import validate, ValidationError

                if prop == 'cookies_schema':
                    got = res.cookies.get_dict()
                if prop == 'json_schema':
                    got = res.json()
                if prop == 'headers_schema':
                    got = res.headers

                try:
                    validate(got, expected)
                except ValidationError as e:
                    errors.append(Error(prop, expected, got, e))
                except Exception as e:
                    sublime.error_message('Schema Error: {}'.format(e))
                    continue

            elif prop in ('cookies', 'json'):  # method equality validation
                count += 1
                if prop == 'cookies':
                    got = res.cookies.get_dict()
                if prop == 'json':
                    got = res.json()
                if got != expected:
                    errors.append(Error(prop, expected, got, 'not equal'))

            else:  # prop equality validation
                if not hasattr(res, prop):
                    continue
                count += 1
                got = getattr(res, prop)
                if got != expected:
                    errors.append(Error(prop, expected, got, 'not equal'))

        result = result + '{} assertion{}, {} error{}\n'.format(
            count, '' if count == 1 else 's',
            len(errors), '' if len(errors) == 1 else 's',
        )
        for error in errors:
            result = result + self.get_error_string(error) + '\n'
        return Result(result, count, len(errors))

    def get_error_string(self, error, max_len=150):
        """Return a one-line string representation of validation error. Attributes
        exceeding `max_len` are truncated.
        """
        error_details = []
        for attr in ['prop', 'expected', 'got', 'error']:
            val = str(getattr(error, attr))
            if len(val) > max_len and not attr == 'error':
                val = '...'
            error_details.append('{}: {}'.format(attr, val))
        return '; '.join(error_details)

    def persist_requests(self, requests):
        """Requests shouldn't be persisted for test runs.
        """
        pass


TEST_MODULE = """# RUN TESTS: `python -m unittest requester_tests`
# MORE INFO: https://docs.python.org/3/library/unittest.html#command-line-interface
# {date}
import unittest

import requests
{imp}

# --- ENV --- #
{env}
# --- ENV --- #


class TestResponses(unittest.TestCase):
{body}


if __name__ == '__main__':
    unittest.main()
"""

INDENT = ' ' * 4


class RequesterExportTestsCommand(TestParserMixin, RequestCommandMixin, sublime_plugin.TextCommand):
    """Parses selected (request, assertion) test pairs and exports them to a
    runnable test script that includes the combined env string built from the env
    file and the env block.
    """
    def make_requests(self, requests, env):
        self.jsi = False  # jsonschema imports necessary?
        tests = []
        for i, test in enumerate(self._tests):
            req = prepare_request(test.request, self._env, i)
            if req.error:
                sublime.error_message('Export Tests Request Error: {}'.format(req.error))
                continue
            try:
                assertion = self.eval_assertion(test.assertion)
            except Exception as e:
                sublime.error_message('Export Tests Assertion Error: {}'.format(e))
                continue
            tests.append(RequestAssertion(req, assertion))

        names = set()
        methods = []
        for test in tests:
            name = self.get_test_name(test, names)
            names.add(name)
            methods.append(self.get_test_method(test, name))
        body = '\n\n'.join(methods)
        body = '\n'.join('{}{}'.format(INDENT, line) for line in body.split('\n'))
        body = '\n'.join('' if line.isspace() else line for line in body.split('\n'))

        date = datetime.datetime.fromtimestamp(time()).strftime('%Y-%m-%d %H:%M:%S')
        jsonschema_import = 'from jsonschema import validate, ValidationError\n'

        view = self.view.window().new_file()
        view.run_command('requester_replace_view_text', {
            'text': TEST_MODULE.format(
                date=date, imp=jsonschema_import if self.jsi else '', env=self._env_string.strip(), body=body
            ), 'point': 0
        })
        view.set_syntax_file('Packages/Python/Python.sublime-syntax')
        view.set_name('requester_tests.py')
        view.set_scratch(True)

    def get_test_method(self, test, name):
        """Return a unittest method string that starts with "def"...
        """
        req, assertion = test
        method = ['def {}(self):'.format(name), 'res = {}'.format(req.request)]
        assertion = {str(k): v for k, v in test.assertion.items()}  # make sure keys can be ordered
        for prop, expected in sorted(assertion.items()):
            if prop in ('cookies_schema', 'json_schema', 'headers_schema'):  # jsonschema validation
                self.jsi = True
                if prop == 'cookies_schema':
                    got = 'res.cookies.get_dict()'
                if prop == 'json_schema':
                    got = 'res.json()'
                if prop == 'headers_schema':
                    got = 'res.headers'
                s = """try:\n{indent}validate({}, {!r})
except ValidationError as e:\n{indent}self.fail(str(e))""".format(
                    got, expected, indent=INDENT
                )

            elif prop in ('cookies', 'json'):  # method equality validation
                if prop == 'cookies':
                    s = 'self.assertEqual(res.cookies.get_dict(), {!r})'.format(expected)
                if prop == 'json':
                    s = 'self.assertEqual(res.json(), {!r})'.format(expected)

            else:  # prop equality validation
                s = 'self.assertEqual(res.{}, {!r})'.format(prop, expected)
            method.append(s)
        return '\n{}'.format(INDENT).join(line for s in method for line in s.split('\n'))

    @staticmethod
    def get_test_name(test, names):
        """Get a unique name for a test method, passing in an iterable of all
        names that have been assigned so far.
        """
        req, assertion = test
        path = parse.urlparse(req.url).path.replace('/', '_')
        method = req.method.lower()
        count = 0
        while True:
            name = 'test_{}{}{}'.format(
                method, clean_var_name(path.replace('/', '_')), '_{}'.format(count) if count else ''
            )
            if name not in names:
                return name
            count += 1


def clean_var_name(s):
    """Clean `s` so that it's a valid Python variable name.
    """
    s = re.sub('[^0-9a-zA-Z_]', '', s)
    s = re.sub('^[^a-zA-Z_]+', '', s)
    return s
