import sublime_plugin


class RequesterAuthOptionsCommand(sublime_plugin.WindowCommand):
    """Allow user to choose an auth snippet and display it in a new view."""

    def run(self, fmt=None):
        self.window.show_quick_panel([s[0] for s in snippets], self.on_done)

    def on_done(self, index: int):
        """Create a view with chosen snippet."""
        if index < 0:  # e.g. user presses escape
            return

        name, content = snippets[index]
        view = self.window.new_file()
        view.set_scratch(True)
        view.run_command("requester_replace_view_text", {"text": content, "point": 0})
        view.set_name("Requester {} Auth".format(name))
        view.set_syntax_file("Packages/Python/Python.sublime-syntax")


snippets = [
    (
        "Basic",
        """requests.get('http://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
""",
    ),
    (
        "Digest",
        """###env
from requests.auth import HTTPDigestAuth
###env

requests.get('http://httpbin.org/digest-auth/auth/user/pass', auth=HTTPDigestAuth('user', 'pass'))
""",
    ),
    (
        "Token",
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
""",
    ),
    (
        "OAuth1",
        """###env
# https://github.com/requests/requests-oauthlib
from requests_oauthlib import OAuth1
auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
###env

get('https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=stackoverflow&count=100', auth=auth)
""",
    ),
    (
        "Cookies Interceptor",
        """###env
import browsercookie
cj = browsercookie.load()  # grabs cookies from firefox and chrome
###env

# if you're currently logged in to github, this request will be logged in as well
get('https://github.com/<myuser>/<myrepo>', cookies=cj)
""",
    ),
]
