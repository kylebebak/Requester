import sublime, sublime_plugin

from collections import namedtuple

from .core import RequestCommandMixin, prepare_request
from .parsers import parse_tests


Error = namedtuple('Error', 'prop, real, expected, error')
Error.__new__.__defaults__ = (None,) * len(Error._fields)


class RequesterTestsCommand(RequestCommandMixin, sublime_plugin.TextCommand):
    """Execute requests from requester file concurrently. For each request with a
    corresponding assertions dictionary, compare response with assertions and
    display all results in one tab.

    Doesn't work for multiple selections.
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
        r = response.response
        errors = []
        for prop, expected in sorted(assertion.items()):
            prop = str(prop) # so lookup with hasattr doesn't explode

            if prop in ('cookies_schema', 'json_schema', 'headers_schema'):
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
                    errors.append(Error(prop, real, expected, e))
                except Exception as e:
                    sublime.error_message('Schema Error: {}'.format(e))
                    continue

            elif prop in ('cookies', 'json'):
                if prop == 'cookies':
                    real = r.cookies.get_dict()
                if prop == 'json':
                    real = r.json()
                if real != expected:
                    errors.append(Error(prop, real, expected))

            else:
                if not hasattr(r, prop):
                    continue
                real = getattr(r, prop)
                if real != expected:
                    errors.append(Error(prop, real, expected))

        results = '{}\n{}\n'.format(response.request, assertion)
        for error in errors:

            error_details = []
            for attr in ['prop', 'expected', 'error']:
                val = getattr(error, attr)
                if val:
                    error_details.append('{}: {}'.format(attr, val))

            if error_details:
                results = results + '\n' + ', '.join(error_details) + '\n'
        return results
