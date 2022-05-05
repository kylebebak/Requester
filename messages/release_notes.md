# 2.39.5

Update path to MarkdownEditing syntax file for Requester: Show Documentation (Local)

# 2.39.4

Fixes bug in parsing --data-raw cURL arg.

# 2.39.3

Changes domain of docs site.

# 2.39.2

Improves `curl_to_request`; to gracefully ignore unknown CURL args.

# 2.39.1

Puts all release notes in this file.

# 2.39.0

## Request parsing

For request parsing errors with non-empty selections, retry parsing with empty selection starting at `region.begin()`.

This improves ergonomics, for example when navigating through requests in a requester files using fuzzy match.

Try highlighting the first 4, 5, 6, 7... characters of this request and then execute it:

get('google.com')

This works for multi-line requests as well. Try highlighting "get(" on the first line, then executing the request.

get(
'google.com'
)

# 2.38.0

## File Downloads

If response content can't be displayed because it's binary, Requester includes instructions for downloading file.

# 2.37.3

## Bug Fix

If response encoding is 'ISO-8859-1' (Latin-1), sets encoding to `response.apparent_encoding`. This gets encoding right in many cases where encoding is not actually Latin-1.

This works around some old, sort of wacky default behavior in Requests: https://github.com/kennethreitz/requests/issues/1604

# 2.37.2

## Bug Fix

Invokes `json.dumps` with `ensure_ascii = False` so that non-ascii chars aren't ascii-encoded in JSON responses.

This improves readability of responses like this one:

requests.get('https://api.partiyaedi.ru/api/v3/goods/actual')

# 2.37.1

## Bug Fix

Fixes strange, possibly non-deterministic context manager bug in `add_path`.

# 2.37.0

## Docs and Error Messages

Adds detailed docs on how env vars are parsed, and improves error messages, most notably for when an env string can't be evaluated successfully because of a missing env var.

Check out "How Env Vars are Parsed" in the docs for more info: https://kylebebak.github.io/Requester/#how-env-vars-are-parsed

# 2.36.0

## New Features

Adds **Requester: Open Request History File** and **Requester: Move Requester File** commands.

The first opens the request history file in a read-only view, and the second moves a requester file to a new path and updates request history for all requests sent from this file.

Also, request history now persists **combined** env string to history file, which means any request can be re-sent even if original requester file is no longer present.

Internal: further improves and simplifies code for computing env and saving to request history file.

# 2.35.0

## New Feature

Improved merging of env block and env file. Concatenation order of strings parsed from env block and env file determined by relative order of env block and `env_file` line in requester file.

Read more in **Merging Vars from Env Block and Env File**.

Internal: cleans up and simplifies `get_env` method.

# 2.34.0

## New Features

Improvement to request history recency weighting.

# 2.33.0

## New Features

Awesome news! I decided to vendor all of Requester's deps, which means you can import `requests_oauthlib` and `requests_toolbelt` in your env block without any mucking around with pip.

It also means that Requester does graphql query autocompletion out of the box.

Requests was also upgraded from 2.15.1 to 2.18.3, which is the last version of the package that supports Python 3.3, the version of Python run by Sublime Text.

For those interested in package development, I'm also working some tooling to make it easy to vendor dependencies for Sublime Text packages. Given the limitations of Package Control, vendoring deps is, as Will Bond says [here](https://github.com/wbond/package_control/issues/825), the "one true approach".

Also fixes a bug in request parsing that was caused by a breaking change in Sublime Text's default Python syntax.

# 2.32.2

## Bug Fixes

Fixes bug due to upgrading Requests from 2.15.1 to 2.18.3. It turns out there is no way to support higher than 2.15.1 using Sublime Text =/

# 2.32.1

## Bug Fixes

Fixes bug due to upgrading Requests from 2.15.1 to 2.18.3. It turns out there is no way to support higher than 2.15.1 using Sublime Text =/

# 2.32.0

## New Features

Awesome news! I decided to vendor all of Requester's deps, which means you can import `requests_oauthlib` and `requests_toolbelt` in your env block without any mucking around with pip.

It also means that Requester does graphql query autocompletion out of the box.

Requests was also upgraded from 2.15.1 to 2.18.3, which is the last version of the package that supports Python 3.3, the version of Python run by Sublime Text.

For those interested in package development, I'm also working some tooling to make it easy to vendor dependencies for Sublime Text packages. Given the limitations of Package Control, vendoring deps is, as Will Bond says [here](https://github.com/wbond/package_control/issues/825), the "one true approach".

Also fixes a bug in request parsing that was caused by a breaking change in Sublime Text's default Python syntax.

# 2.31.0

## New Features

When deleting a request from Requester history, requester pages to the previous request, which gives user immediate visual feedback that request has been deleted.

Also includes `[ctrl+alt+delete]` binding in history tab, so that users are aware this function exists.

Closes <https://github.com/kylebebak/Requester/issues/19>.

# 2.30.0

## New Features

Requester history search has been updated to weight recent request history matches more heavily. This makes history search more predictable and more intuitive.

Closes <https://github.com/kylebebak/Requester/issues/18>.

# 2.29.0

## New Features

Requester's parser has been updated to parse prepared requests. Sending prepared requests can be useful for, e.g., sending requests with a self-signed certificate. Read more in the **Sessions** section of the docs, or here:

http://docs.python-requests.org/en/master/user/advanced/#prepared-requests

# 2.28.0

## New Features

Single requests that don't start at the first character of a line can be parsed correctly. This allows you, for example, to execute requests that have been commented out, or requests that are in doc strings, or requests in a markdown list.

Place your cursor on the first line of either of these requests and attempt to execute them.

- get('google.com')

* get('httpbin.org/get',
  params={'a': 'b'}
  )

# 2.27.2

## Bug Fix

**Explore URL in Response Tab** command works for localhost URLs.

# 2.27.1

## Bug Fix

Fixes a bug in **Import from cURL**; parser can now handle "#" characters.

# 2.27.0

## New Features

The **tabname** argument is now included in the fuzzy searchable request history, which makes is considerably more useful.

Check out the **Custom Tab Name** section of the docs for more info.

# 2.26.0

## New Features

Requester requests support a new keyword argument, **tabname**, that allows you to specify a custom response tab name for a request. This response tab can only be overwritten by requests with the same **tabname**.

This is useful for differentiating requests whose method and URL are the same but whose meaning is different. GraphQL requests, whose meaning is encoded in the query string, are one example.

# 2.25.0

## New Features

Requester's Test Runner now supports **custom validation functions**, which allow you to make assertions about any aspect of response object using anything Python has to offer.

This is a feature I've wanted to add for a long time. I hope you all like the implementation. Check out the docs to see how it works.

Also, Export to cURL now supports basic authentication.

# 2.24.1

## New Feature/Bug Fix

File downloads don't always display '?' for content length. First, `content-length` header is inspected, and if it's empty, length of response is taken.

# 2.24.0

## New Feature

Multiline requests can now be executed by placing cursor **anywhere** inside the request, not just on the first line, thanks again to @jcberquist =)

This works as long as the view's syntax recognizes Python function calls.

# 2.23.1

## Optimization

Requester doesn't save `original_request` to history file if it's the same as `request`. This decreases size of Requester file.

# 2.23.0

## New Features

Requests are saved to history with original value of request sent from requester file.

This means saving requests back to requester file works for requests loaded from history, even if these requests were edited in the response tab.

# 2.22.0

## New Features

Requests in history are now keyed for uniqueness on `(request_string, requester_file)`, instead of just `request_string`, if the requester file exists.

Also, a request can be deleted from request history by pressing `ctrl+alt+backspace` in the request's history tab.

Finally, there are several improvements to file downloads:

- downloads don't require a '/' suffix for Requester to automatically assign the file a name
- downloads correctly resolve the '~' char to the user's home directory
- downloads from URLs with a trailing query string get the correct file extension

# 2.21.1

## Bug Fixes

Much better syntax highlighting for requester files, thanks to @jcberquist!

Also, fixed bug in explore request command, which choked on requests with a dangling, trailing comma.

# 2.20.0

## New Features

Response tab name: if parsed URL has no `path`, display `netloc` (base path), instead of displaying nothing.

Also, the default length of response tab names is limit to 32 characters. You can change this limit in settings.

## Bug Fixes

Fixed bug in saving requests back to requester file when paging through request history.

# 2.19.2

## Bug Fix

It's taken me a while to get "save request back to requester file" exactly right, but it's finally good to go.

This fixes a bug that would replace either too many or too few characters in the original response view.

# 2.19.1

## New Features/Bug Fix

Not exactly new features or a bug fixes, but saving requests back to the requester file was significantly improved and simplified.

- You can save back requests even if your requester file has been modified in the meantime. Save will only fail if the original request itself has been modified.
- You can now save back requests that you load from your history file.
- Scrolling to the original request now works reliably even if the requester file isn't currently open when you save back your request.

# 2.19.0

## New Features

You can save a modified request in a response tab back to the Requester file from which you sent it!

- Can be used repeatedly in response view.
- Guaranteed to old overwrite old request and nothing else.

Also, the default length of response tab names is limit to 32 characters. You can change this limit in settings.

## Bug Fixes

Requester doesn't print error messages to status bar if requester file contains non-ascii chars.

# 2.18.0

## New Features

Serious GraphQL support! Requester can autocomplete any GraphQL query from a response tab.

- Autocomplete provides field type, name, and arguments, similar to [GraphiQL](https://github.com/graphql/graphiql).
- Enable autocomplete by installing `graphql-py` using `pip`, see documentation for extending Requester.

As far as I know, Requester make Sublime Text the first text editor with reliable GraphQL support!

# 2.17.0

## New Features

- Added basic GraphQL support

  - `gql`, `gqlv`, and `gqlo` kwargs to automatically add GraphQL queries to querystring for GET requests, and to JSON encoded request body for POST requests.
  - GraphQL autosuggest coming soon!

- Added `browsercookie` auth option for grabbing Chrome/Firefox cookies and adding them to requests, similar to Postman's Interceptor.
  - Added information on importing Python libraries that depend on shared objects, like `pycyrpto`.

## Bug Fixes

Extending Requester: no longer writes writes same `packages_path` to `sys.path` multiple times.

# 2.16.0

## New Features

Test coverage was improved significantly. Also, Requester now has a docs site! Check it out at <https://kylebebak.github.io/Requester/>, or by running **Requester: Show Documentation (Online)**.

# 2.15.0

## New Features

Requester's on fire! Request history has been totally revamped for this version, combining fuzzy search with paging for request history nirvana.

### Request History

If you run **Requester: Request History** from the command palette (add this to your key bindings, the command is "requester_history"), you get the usual fuzzy searchable list of requests. But now, if you select one of these requests and hit Enter, Requester doesn't execute the request.

Instead, it "stages" the request into a "request history" tab, from which you can look at the request and edit it before you execute it. And if you press `ctrl+alt+ ←/→`, you can page between requests that were executed before and after this historical request.

You can actually start paging through past requests from any open response tab.

Being able to stage requests before executing them is a big help for requests that aren't idempotent, like POST requests... Before you had to execute them to even see them.

And paging combined with search makes it trivial to find past requests. If it's a recent request, just start paging backwards. If it was a week ago, and you know it was one of many you executed against the Twitter API, fuzzy search for "twitter" to land in the general neighborhood, then page around to find the exact one you're looking for.

### Little Improvements

- Ergonomics for basic GET requests: parser handles URLs with or without wrapping quotes.

# 2.14.0

## New Features

More good news! Like 2.13.0, this release introduces a number of improvements to Requester.

- File downloads whose path has no `basename` get an automatically generated filename. If the filename is already take, a new unique filename is generated.

  - Also removed a subtle bug in downloads.

- Requests defined over multiple lines are much easier to execute. You can place cursor anywhere on the first line of a multi-line request and run it without highlighting anything.

- Requester has a new option to "explore" URLs returned in the response body of a request. Highlight a URL in a response tab and press `ctrl+e` (`cmd+e` on macOS) to send a GET request to the highlighted URL.
  - If the URL has the same domain as the URL for the original request, the rest of the request args will are left unchanged, which means that the new request will be trivially authenticated.
  - If the URL has a different domain, the remaining args are removed from the new request.

## Bug Fixes

- Requests executed from a requester file pull in the current values for all env vars in this file, **even if the file has not yet been saved**.

# 2.13.0

## New Features

Great news! This release introduces some cool improvements to Requester.

- Requester can now source **any** Python 3 package in its env! All you have to do is set the `packages_path` setting to a directory with Python 3 packages you'd like to include with Requester, e.g. to a virtualenv directory: `~/.virtualenvs/general/lib/python3.5/site-packages`.

  - Use any plugin in the Python ecosystem, including any auth plugin
    - `requests-oauthlib`, "https://github.com/requests/requests-oauthlib"
  - Use `requests-toolbelt`, "https://github.com/requests/toolbelt"
  - the `requests` and `jsonschema` packages are obviously still bundled with Requester

- Sending basic GET requests just got more convenient. Selections spanning only one line, of the form `http://google.com` or `google.com` are now transformed to `get('http://google.com')` before being sent by Requester.

- Added request navigation, request groups, and improved syntax highlighting to requester files, as long as they are saved with the `.pyr` extension
  - You can jump between requests using fuzzy search using the **Goto Symbol** command
  - Running **Requester: New Requester File** from the command palette creates a file with this extension, and sets the **Requester** syntax on the view
  - Read more in the **Request Navigation** section of the README

# 2.12.0

## New Features

Multiple file uploads and downloads can be executed in parallel.

## Code

Access to persist_requests function is controlled by a lock, to make sure threads concurrently executing this function don't corrupt request history. Also, fixed small bug in importing requests from cURL.

# 2.11.0

## New Features

Any method can be used to start a file download, not just GET.

# 2.10.0

## New Features

File uploads and downloads are persisted to request history, and downloads get their own response tabs.

## Code

Fixed race condition bug in uploads and downloads, where env was being referenced before it had been evaluated.

# 2.9.1

## Code

Fixed a bug for uploads: Requester now displays an error message if the file being uploaded doesn't exist.

# 2.9.0

## New Features

Support for streamed and chunked file uploads enabled via simple `streamed` and `chunked` special kwargs.

# 2.8.0

## New Features

Improvement to request chaining: users can "name" response to requests and reference those responses by name in subsequently executed requests.

Added `fmt` argument to requests, which controls JSON response formatting. It can be one of one of ('raw', 'indent', 'indent_sort').

Improved syntax highlighting for response views with no valid content type in response headers.

## Code

Reorganized project so that command files, and syntax files, each have their own directory. All command files are loaded by top-level `requester.py` module.

# 2.7.0

## New Features

Users can specify in settings whether or not to `allow_redirects` by default.

## Code

Fixed bug in `get_exports` helper.

# 2.6.0

## New Features

Added **Requester: Authentication Options** command, which contains a reference for common auth schemes to use in requests. Added some support for more cURL options when importing requests from cURL. Added **Requester: Settings** command to command palette.

## Code

Bug fixes for importing requests from cURL, including a bug that caused Sublime Text to hang indefinitely.

# 2.5.0

## New Features

Added function to export selected request/assertion pairs to a runnable test script that can be integrated into a test routine. Also, exporting to HTTPie now supports sessions.

## Code

Simplified code in `RequestCommandMixin.get_env` that handles building environment dictionary.

# 2.4.1

## New Features

## Code

Fixed regression that broke chaining requests by reference.

# 2.4.0

## New Features

Added **export to HTTPie** command.

## Code

Fixed subtle bugs in arg parsing for export commands. Also made error messages more explicit for certain syntax and parsing errors.

# 2.3.0

## New Features

Added **export to cURL** and **import from cURL** commands.

## Code

Fixed bug with `requests` args that had a trailing comma, re-executing these requests from response tab used to raise exception.

# 2.2.0

## New Features

Requester supplies default `http` scheme if no scheme is specified in URL.

# 2.1.0

## New Features

Improved syntax highlighting for test run views.

## Code

Fixed performance issues with benchmark runs, and fixed potential race conditions with pending requests.

# 2.0.0

## New Features

Added request benchmarking tool, similar to ab and siege. Check the README for details.

## Code

New major version. Rewrote core API and parser so that eval is only called once per request, to extract args and kwargs from request string. Among other things, this means that method and URL, along with args and kwargs passed to requests, are known before response returns.

Building new clients of the core API, such as the new benchmarking tool, is much easier.

Also, various small bug fixes.

# 1.17.0

## New Features

Display request body in response tab, if body was present.

## Code

Fixed comment/backslash bug in parser.

# 1.16.0

## New Features

## Code

Improved `persist_requests`. Requester creates a backup of request history, and will not lose requests if an exception is raised or there is a crash while file is being written to.

There is now no possibility of request history being lost, minus the user deleting his request history file.

# 1.15.0

## New Features

Improvements to request parser: parser doesn't choke on escaped single quotes or escaped double quotes.

Added **pin_tabs_by_default** setting, which allows users that don't want any reponses to be overwritten to pin newly opened response tabs by default.

## Code

Improved behavior of `RequesterCancelRequestsCommand`.

# 1.14.0

## New Features

Added command to **pin/unpin** response tabs.

Unpinned response tabs are overwritten by requests with the same method and URL. Pinned response tabs are not, which makes it possible to have multiple views open for the same request.

To pin/unpin a response tab, hit `cmd+t` on OSX, or `ctrl+t` on Linux/Windows.
