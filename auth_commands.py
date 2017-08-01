import sublime_plugin


class RequesterAuthOptionsCommand(sublime_plugin.WindowCommand):
    """Parse `num` and `concurrency` from user input and pass them to
    `RequesterBenchmarksCommand`.
    """
    def run(self, fmt=None):
        self.window.show_quick_panel([s[0] for s in snippets], self.on_done)

    def on_done(self, index):
        """Callback for invokes request chosen from quick panel.
        """
        if index < 0:  # e.g. user presses escape
            return

        name, content = snippets[index]
        view = self.window.new_file()
        view.set_scratch(True)
        view.run_command('requester_replace_view_text', {'text': content, 'point': 0})
        view.set_name('Requester {} Auth'.format(name))
        view.set_syntax_file('Packages/Python/Python.sublime-syntax')


snippets = [
    (
        'Basic',
        """requests.get('http://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
"""
    ),
    (
        'Digest',
        """###env
from requests.auth import HTTPDigestAuth
###env

requests.get('http://httpbin.org/digest-auth/auth/user/pass', auth=HTTPDigestAuth('user', 'pass'))
"""
    ),
    (
        'Token',
        """###env
class TokenAuth:
    def __init__(self, auth_prefix, token):
        self.auth_prefix = auth_prefix  # e.g. 'Bearer'
        self.token = token

    def __call__(self, r):
        r.headers['Authorization'] = '{0} {1}'.format(self.auth_prefix, self.token).strip()
        return r
###env

requests.get('http://httpbin.org/headers', auth=TokenAuth('Bearer', 'big_auth_token'))
"""
    ),
]
