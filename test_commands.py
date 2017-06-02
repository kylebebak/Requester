import sublime, sublime_plugin

from collections import namedtuple

from .core import RequestCommandMixin
from .core.parsers import parse_tests, prepare_request


Error = namedtuple('Error', 'prop, expected, real, error')


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

        timeout = self.config.get('timeout', None)
        requests = []

        for test in self._tests:
            r = prepare_request(test.request, timeout)
            requests.append(r)

        return requests

    def handle_responses(self, responses):
        """Compares response objects with assertions dictionaries and displays a
        test run view that includes all discrepancies.
        """
        if len(self._tests) != len(responses):
            sublime.error_message('Parse Error: something went wrong')
            return

        errors = []
        results = []
        for i, response in enumerate(responses):
            try:
                assertion = self.eval_assertion(self._tests[i].assertion)
            except Exception as e:
                errors.append( '{}: {}'.format('Assertion Error', e) )
            else:
                results.append(self.get_results(response, assertion))

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

        view.run_command('requester_replace_view_text',
                         {'text': '\n\n'.join(results), 'point': 0})
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

    def get_results(self, response, assertion):
        """Get results of comparing response with assertion dict. Ignores keys in
        assertion dict that don't correspond to a valid property or method of
        response.
        """
        results = '{}\nassert {}\n'.format(response.request, assertion)
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
                    real = r.cookies.get_dict()
                if prop == 'json_schema':
                    real = r.json()
                if prop == 'headers_schema':
                    real = r.headers

                try:
                    validate(real, expected)
                except ValidationError as e:
                    errors.append(Error(prop, expected, real, e))
                except Exception as e:
                    sublime.error_message('Schema Error: {}'.format(e))
                    continue

            elif prop in ('cookies', 'json'): # method equality validtion
                count += 1
                if prop == 'cookies':
                    real = r.cookies.get_dict()
                if prop == 'json':
                    real = r.json()
                if real != expected:
                    errors.append(Error(prop, expected, real, 'not equal'))

            else: # prop equality validation
                if not hasattr(r, prop):
                    continue
                count += 1
                real = getattr(r, prop)
                if real != expected:
                    errors.append(Error(prop, expected, real, 'not equal'))

        results = results + '{} prop{plural}, {} error{plural}\n'.format(
            count, len(errors), plural='' if count == 1 else 's')
        for error in errors:
            results = results + self.get_error_string(error) + '\n'
        return results

    def get_error_string(self, error, max_len=150):
        """Return a one-line string representation of validation error. Attributes
        exceeding `max_len` are truncated.
        """
        error_details = []
        for attr in ['prop', 'expected', 'real', 'error']:
            val = str(getattr(error, attr))
            if len(val) > max_len:
                val = '...'
            error_details.append('{}: {}'.format(attr, val))
        return '; '.join(error_details)
