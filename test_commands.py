import sublime, sublime_plugin

from collections import namedtuple

from .core import RequestCommandMixin
from .core.parsers import parse_tests


Error = namedtuple('Error', 'prop, expected, got, error')
Result = namedtuple('Result', 'result, assertions, errors')


class RequesterRunTestsCommand(RequestCommandMixin, sublime_plugin.TextCommand):
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
            except:
                sublime.error_message('Parse Error: unbalanced brackets in tests')
            break # only parse first selection

        return [test.request for test in self._tests]

    def handle_responses(self, responses):
        """Compares response objects with assertions dictionaries and displays a
        test run view that includes all discrepancies.
        """
        if len(self._tests) != len(responses):
            sublime.error_message('Parse Error: something went wrong')
            return

        results = []; errors = []
        count_assertions = 0; count_errors = 0
        for i, response in enumerate(responses):
            try:
                assertion = self.eval_assertion(self._tests[i].assertion)
            except Exception as e:
                errors.append( '{}: {}'.format('Assertion Error', e) )
            else:
                r = self.get_result(response, assertion)
                count_assertions += r.assertions
                count_errors += r.errors
                results.append(r.result)

        if errors:
            sublime.error_message('\n\n'.join(errors))
        if not results: # don't open test view if no tests were run
            return

        view = self.view.window().new_file()
        view.set_scratch(True)
        view.settings().set('requester.test_view', True)
        view.settings().set('requester.env_string',
                            self.view.settings().get('requester.env_string', None))
        view.settings().set('requester.env_file',
                            self.view.settings().get('requester.env_file', None))

        header = '-- {} assertion{}, {} error{} --\n'.format(
            count_assertions, '' if count_assertions == 1 else 's',
            count_errors, '' if count_errors == 1 else 's',
        )
        view.run_command('requester_replace_view_text',
                         {'text': header + '\n\n' + '\n\n'.join(results), 'point': 0})
        view.set_name('Requester Test Run')
        view.set_syntax_file('Packages/Requester/requester-test.sublime-syntax')

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

    def get_result(self, response, assertion):
        """Get result of comparing response with assertion dict. Ignores keys in
        assertion dict that don't correspond to a valid property or method of
        response.
        """
        result = '{}\nassert {}\n'.format(response.request, assertion)
        r = response.response
        errors = []
        count = 0

        assertion = {str(k): v for k, v in assertion.items()} # make sure keys can be ordered
        for prop, expected in sorted(assertion.items()):
            prop = str(prop) # so lookup with hasattr doesn't explode

            if prop in ('cookies_schema', 'json_schema', 'headers_schema'): # jsonschema validation
                count += 1
                from jsonschema import validate, ValidationError

                if prop == 'cookies_schema':
                    got = r.cookies.get_dict()
                if prop == 'json_schema':
                    got = r.json()
                if prop == 'headers_schema':
                    got = r.headers

                try:
                    validate(got, expected)
                except ValidationError as e:
                    errors.append(Error(prop, expected, got, e))
                except Exception as e:
                    sublime.error_message('Schema Error: {}'.format(e))
                    continue

            elif prop in ('cookies', 'json'): # method equality validtion
                count += 1
                if prop == 'cookies':
                    got = r.cookies.get_dict()
                if prop == 'json':
                    got = r.json()
                if got != expected:
                    errors.append(Error(prop, expected, got, 'not equal'))

            else: # prop equality validation
                if not hasattr(r, prop):
                    continue
                count += 1
                got = getattr(r, prop)
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
