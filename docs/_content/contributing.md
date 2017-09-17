# Contributing
Please do! Possible improvements:

- Add snippets and docs for more auth schemes
  + OAuth 1
  + OAuth 2
- More export/import formats
  + HTTP
  + Downloads to Wget
- Improved support for GraphQL
- Randomized requests with benchmark runs (e.g. for fuzz testing)
- Tell your friends about Requester!


## How Does It Work?
The core API is defined in modules under the `core` directory. The main class is `RequestCommandMixin`.

This mixin is the motor for parsing an env, executing requests in parallel in the context of this env, invoking activity indicator methods, and invoking response handling methods. These methods can be overridden to control the behavior of classes that inherit from this mixin.

The mixin uses the `ResponseThreadPool` class, which wraps a thread pool to execute requests in parallel. Default concurrency is determined by the mixin's `MAX_WORKERS` class property. The thread pool is inspected at regular intervals to remove completed responses and handle them, and show activity for pending requests.

Command classes that use this mixin can override `handle_response` and/or `handle_responses`. This way they can handle responses one at a time as they are completed, or as a group when they're all finished. Each response object contains a `req` namedtuple with a bunch of useful properties, the `res` (a __requests.Response__ object), and an `err` string. Responses are sorted by request parsing order.

Command classes __must__ also override `get_requests`, which must return a list of request strings, for example strings parsed from the current view. To simplify this, `core` has a `parsers` module. The important parser is `parse_requests`. It takes a string, such as a selection from a view, and returns a list of all requests in the string.


### Writing a New Command Class
If you want to write a new command class for Requester, check out how `RequesterCommand` works; it simply uses the mixin and overrides `get_requests` and `handle_response`.

If you want a better understanding of the details, dive into `core` directory. This is where the heavy lifting is done.


## Python Linting and Code Style
Uses __flake8__. First, install __flake8__ with `pip3 install flake8`.

Read how to set up a pre-commit hook [here](http://flake8.pycqa.org/en/latest/user/using-hooks.html), or just keep reading.

Run `flake8 --install-hook git`, and check that `.git/hooks/pre-commit` was created. Then run `git config --bool flake8.strict true`, and check that this worked by running `git config --get --bool flake8.strict`. It should return __true__.

You will now be unable to commit anything that doesn't pass __flake8__ validation.

All classes and methods should have docstrings, limited to 82 characters per line. Except for `run` and `__init__`. Feel free to add comments for anything that's not obvious.


## Tests
Tests are divided into tests of the `core` package, which depend on a mocked `sublime` and are run in Travis, and integration tests run within Sublime Text.

Many tests for Requester are asynchronous, because they depend on responses coming back before examining response tabs. For this reason, tests are executed against a local server powered by __httpbin__. You can install __httpbin__ by running `pip install httpbin`. You can then run it with `gunicorn httpbin:app` or `gunicorn --access-logfile /dev/stdout httpbin:app`.

To run `core` tests, execute `python -m unittest tests.core -v` from the root of the repo. 

To run the integration tests, install __UnitTesting__ via Package Control. Read more about [UnitTesting](https://github.com/randy3k/UnitTesting-example). Also, make sure you've cloned the Requester repo into your __Packages__ directory.

Run integration tests before committing changes. Look for __UnitTesting__ in the command palette, hit enter, and type `Requester`. Or, if you've created a project for Requester, run __UnitTesting: Test Current Project__.
