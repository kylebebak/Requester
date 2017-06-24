# Contributing
Please do! Possible improvements:

- Improve test runner
  + Run tests in a requester file from command line, so that they can be integrated into an arbitrary test suite
  + Alternatively, create command to export requests and assertions in requester file to a runnable Python test script
  + Better syntax highlighting for test run results view
- Create a clone of [ab](http://httpd.apache.org/docs/current/programs/ab.html)
  + Allow user to specify `number_of_requests` and `concurrency` when invoking command
  + Display results
  + This should be easy given the API provided by `RequestCommandMixin`
- Import from and export to common request formats (HTTP, cURL, etc)
- Generate API documentation from JSON Schema
- Creating tutorial videos showing Requester in action
- Better test coverage
  + Tests for error messages
  + Tests for proper parsing of env block and env files
  + Tests for activity indicators
  + Tests for syntax files
  + Tests for test runner
  + Tests for request history
  + Tests for file downloads


## How Does It Work?
The core API is defined in modules under the `core` directory. The main class is `RequestCommandMixin`.

This mixin is the motor for parsing an env, executing requests in parallel in the context of this env, invoking activity indicator methods, and invoking response handling methods. These methods can be overridden to control the behavior of classes that inherit from this mixin. It must be mixed in to classes that also inherit from `sublime_plugin.TextCommand`.

The mixin uses the `ResponseThreadPool` class, which wraps a thread pool to execute requests in parallel. Default concurrency is determined by the mixin's `MAX_WORKERS` class property. The thread pool is inspected at regular intervals to remove completed responses and handle them, and show activity for pending requests.

Command classes that use this mixin should override `handle_response` and/or `handle_responses`. This way they can handle responses one at a time as they are completed, or as a group when they're all finished. Each response object contains the parsed `request` string, the `response` (a __requests.Response__ object), an `error` string, and an `ordering`. Responses are sorted by request parsing order before they are passed to `handle_responses`.

Command classes __must__ also override `get_requests`, which must return a list of request strings parsed from the current view. To simplify this, `core` has a `parsers` module. The most important parser is `parse_requests`. It takes a string, such as a selection from a view, and returns a list of all requests in the string.


### Writing a New Command Class
If you want to write a new command class for Requester, check out how `RequesterCommand` works; it simply uses the mixin and overrides `get_requests` and `handle_response`.

If you want a better understanding of the details, dive into `core` directory. This is where the heavy lifting is done.


## Python Code Style
Try to limit lines to 100 characters or less, unless doing so is inconvenient. No lines with more than 120 characters.

Two lines between classes or top-level methods. One line between class methods. Within methods, use vertical whitespace if it improves readability, but never more than one line.

Indentation: 4 spaces. No tabs.

All classes and methods should have docstrings, limited to 82 characters per line. Except for `run` and `__init__`. Feel free to add comments for anything that's not obvious.


## Tests
Install __UnitTesting__ via Package Control. Read more about [UnitTesting](https://github.com/randy3k/UnitTesting-example). Also, make sure you've cloned the Requester repo into your __Packages__ directory.

Run tests before committing changes. Look for __UnitTesting__ in the command palette, hit enter, and enter `Requester`. Or, if you've created a project for Requester, run __UnitTesting: Test Current Project__.

Many tests for Requester are asynchronous, because they depend on responses coming back before examining response tabs. This means tests may fail simply because a response wasn't returned on time. This is a false positive, just run the tests again.

This is also why I'm reluctant to use something like Travis, because the build may fail even when nothing is wrong with the package.
