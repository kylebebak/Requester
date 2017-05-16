## Contributing
Please do! Areas for improvement:

- better test coverage, with a focus on integration tests rather than unit tests
- better syntax highlighting in response tabs (this idea from keith-hall)
- creating a testing framework that allows users to make assertions about response content for given requests, perform test runs and view results


### Python Code Style
Try to keep lines 100 characters or less, unless doing so is very inconvenient. No lines more than 120 characters.

Two lines between classes or top-level methods. One line between class methods. Within methods, use vertical whitespace if it improves readability, but never more than one line.

All classes and methods should have docstrings, limited to 82 characters per line. Except for the `run` method. Add inline comments for anything that's not obvious.


## Tests
Install __UnitTesting__ via Package Control. Read more about [UnitTesting](https://github.com/randy3k/UnitTesting-example).

Make changes, and before committing them run tests. Look for __UnitTesting__ in the command palette, hit enter, and enter `Requester`. Or, if you've created a project for Requester, run __UnitTesting: Test Current Project__.

Many tests for Requester are asynchronous, because they depend on responses coming back before examining response tabs. This means tests may fail simply because a response wasn't returned on time. This is a false positive, just run the tests again.
