# Requester: HTTP Client for Humans

![License](https://camo.githubusercontent.com/890acbdcb87868b382af9a4b1fac507b9659d9bf/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)

A modern, team-oriented HTTP client for Sublime Text 3, built on top of [Requests](http://docs.python-requests.org/en/master/). Requester combines features of apps like Postman, Paw and HTTPie, and improves on them wherever possible.

Get environment variables, concurrent requests, multiple, editable response tabs and the beautiful syntax of Requests, all without neutering your keyboard. You should honestly try it even if you've never used Sublime Text.


## Features
- [Elegant, well-documented syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + Easily set request body, query params, custom headers, cookies
  + Support for sessions, authentication
  + Forms and file uploads, Wget-style downloads  
  + HTTPS, proxies, redirects, and more
- Intuitive, modern UX
  + Environment variables
  + Execute requests and display responses in parallel, or chain requests
  + Edit and replay requests from individual response tabs
  + Replay requests from fuzzy searchable request history
  + Formatted, colorized output
  + Automatic syntax highlighting and pretty printing
  + Clear error handling and error messages
- Perfect for teams
  + Sharing and versioning of requests and env vars
  + Lightweight, integrated test runner with support for JSON Schema


## Installation
1. Download and install [Sublime Text 3](https://www.sublimetext.com/3).
2. Install [Package Control for Sublime Text](https://packagecontrol.io/).
3. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
4. Search for __Requester__ (not ~~Http Requester~~) and install it.
5. __If you're seeing errors__ every time you run a request, this probably means the __requests__ dependency wasn't installed successfully. To fix this, look for __Package Control: Satisfy Dependencies__ in the command palette, run it, and restart Sublime Text.


## Getting Started
>An interactive version of this tutorial is also available. Look for __Requester: Show Tutorial__ in the command palette.

Open a file and insert the following:
~~~py
requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

get('https://jsonplaceholder.typicode.com/posts')
post('https://jsonplaceholder.typicode.com/posts')
~~~

Place your cursor on one of the lines and hit <kbd>ctrl+alt+r</kbd> (<kbd>ctrl+r</kbd> on OSX). Or, look for __Requester: Run Requests__ in the command palette and hit Enter. A response tab will appear, with a name like __GET: /albums__.

Head to the response tab and check out the response. Hit <kbd>ctrl+alt+r</kbd> or <kbd>ctrl+r</kbd> (<kbd>ctrl+r</kbd> or <kbd>cmd+r</kbd> on OSX) to replay the request. You can edit the request, which is at the top of the file, before replaying it.

Now, go back to the requester file and highlight all 5 lines, and once again execute the requests.

Tabs will open for all 4 requests (Requester conveniently ignores the blank line). Before checking out these tabs, execute the requests yet again. You'll notice duplicate requests don't create a mess of new tabs, but simply overwrite the content in the matching response tabs.

Want to see something nifty? Mix up the order of the 4 open response tabs, come back to your requester file, and run __Requester: Reorder Response Tabs__.

If you want to define requests over multiple lines, just make sure you fully highlight the requests before executing them. Try it.

~~~py
get(
  'https://jsonplaceholder.typicode.com/posts'
)
post(
  'https://jsonplaceholder.typicode.com/posts'
)
~~~

Prefixing your requests with __requests.__ is optional. If you want to close all open tabs, look for __Requester: Close All Response Tabs__ in the command palette.


### Environment Variables
It's time to add environment variables to your requests. Requester lets you to do this directly in your requester file. Just put your environment variables in a code block fenced by __###env__ lines.

~~~py
###env
base_url = 'https://jsonplaceholder.typicode.com'
###env

requests.get(base_url + '/albums')
requests.post(base_url + '/albums')
~~~

Try executing these requests. Nice, huh?

The __###env__ lines must have no leading or trailing spaces. Only the first env block in a requester file will be used.


## Advanced Features
Find out what makes Requester really special. In the future if you need to refresh your memory, just press <kbd>shift+cmd+p</kbd> to open the command palette, and type __Requester__.


### Separate Env File
Requester also lets you save and source your env vars from a separate env file. To do this, first you want to save your requester file. This way you can use a __relative path__ from your requester file to your env vars file, which is convenient. Save it with any name, like `requester.py`.

Next, save a file with the name `requester_env.py` in the same directory as `requester.py`, and add an env var to it.

~~~py
base_url = 'https://jsonplaceholder.typicode.com'
~~~

Finally, define the path of your `env_file` in your requester file like so:

~~~py
env_file = 'requester_env.py'

requests.get(base_url + '/albums')
requests.post(base_url + '/albums')
~~~

Requester will now look for the env file at the path `requester_env.py`, which is relative to the location of the requester file. You can change this path to any relative path you want, e.g. `relative/path/to/env.py`. You can also use an __absolute path__ to the env vars file if you want.


#### Merging Vars from Env Block and Env File
Is totally fine. If a var has the same name in the env block and the env file, the var from the env file takes precedence.

Why? If you're working on a team, your requester file should probably be in version control. Static env vars and default values for dynamic env vars can be defined in the env block of your requester file.

Dynamic env vars, like a `base_url` that might point to staging one minute and production the next, can be (re)defined in an env file. Put the env file in your `.gitignore`. This way devs can tweak their envs without making useless commits or stepping on each other's toes.


### Request Body, Query Params, Custom Headers, Cookies
~~~py
get('http://httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/redirect-to?url=foo')
# response tab shows redirects
~~~

Body, Query Params, and Headers are passed to __requests__ as dictionaries. Cookies can be passed as a dict or an instance of `requests.cookies.RequestsCookieJar`.

If you execute the last request, you'll notice the response tab shows the series of redirects followed by the browser.

If you don't know how to do something, check out __Requester: Show Tutorial__ from the command palette, or review syntax at the [Requests Quickstart](http://docs.python-requests.org/en/master/user/quickstart/).


### New Requester File
Want to start a new collection of requests? Run __Requester: New Requester File__ from the command palette. You'll get a new file pointing to an empty env file, with an empty env block, and with a link to Requester's syntax at the top.


### Sessions
Need to log in first so all your requests include a session cookie? [Session objects](http://docs.python-requests.org/en/master/user/advanced/#session-objects) make this a cinch. 

Instantiate the session object in the env block and use it in your requests. Copy this code to a new file and give it a try.

~~~py
###env
import requests
s = requests.Session()
s.get('http://httpbin.org/cookies/set?session_id=12345', timeout=5)
###env

s.get('http://httpbin.org/get')
~~~


### Forms and File Uploads
Requests makes both of these tasks trivial. See how in the Requests Quickstart:

- Forms: <http://docs.python-requests.org/en/latest/user/quickstart/#more-complicated-post-requests>
- File uploads: <http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file>


### Downloads
Requester also provides Wget-style downloads. Just add the `filename` keyword arg to a call to `requests.get`.

~~~py
requests.get('http://www.nationalgeographic.com/content/dam/animals/thumbs/rights-exempt/mammals/d/domestic-dog_thumb.jpg', filename='image.jpg')
~~~

`filename` can be an absolute path, or a path relative to your requester file. Downloads can be cancelled. They come with a nice progress bar.


### Cancel Outstanding Requests
If you have outstanding requests that are taking a while to return, and you don't want to wait for them to time out, you can cancel them by calling __Requester: Cancel Requests__ from the command palette.


### Request History
Requester saves a history of executed requests. Call __Requester: Request History__ to check it out. They appear in reverse chronological order and include each request's age, URL, response status code, and requester file. They're fuzzy searchable!

Choose an old request and run it. It runs as if it were executed from its original requester file, with access to up-to-date env vars defined in the env block and the env file. It's one of Requester's most convenient features, which means you might want to modify your keymap and bind something to __requester_history__.

Open your keymap from the command palette by running __Prefences: Key Bindings__. For example, on OSX you might bind it to <kbd>ctrl+h</kbd> by adding the following:

~~~json
{ "keys": ["ctrl+h"], "command": "requester_history" },
~~~


### Test Runner
Requester has a built-in test runner! Copy and paste this into an empty file.

~~~py
###env
base_url = 'https://jsonplaceholder.typicode.com'
prop = 'status_code'
###env

# first request
requests.get(
  base_url + '/posts'
)
assert {prop: 200, 'encoding': 'utf-8'}

# second request, with no assertion
requests.get(base_url + '/profile')

# third request
requests.get(base_url + '/comments')

assert {
  'status_code': 500
}
~~~

Highlight all the requests, look for __Requester: Run Tests__ in the command palette, and run it. You'll notice that test results are displayed for the first and third requests.

What's going on here? If a request has an assertion below it, the `key, value` pair in the assertion is compared with the returned `Response` object. If `key` is a valid property of the `Response` object, `value` is compared with the property. If they're not equal discrepancies are displayed.

Some valid properties: `apparent_encoding`, `cookies`, `encoding`, `headers`, `history`, `is_permanent_redirect`, `is_redirect`, `json`, `links`, `reason`, `status_code`, `text`, `content`.

`cookies`, `headers` and `json` point to Python dicts or lists, which means comparing for equality isn't very useful. Much more useful are the following special assertion keys for these properties: `cookies_schema` `headers_schema` `json_schema`.

Including one of these in an assertion will validate the corresponding property with [jsonschema.validate](https://github.com/Julian/jsonschema). If you have a JSON API, [JSON Schema](http://json-schema.org/) is an excellent way to describe your API's data format. Use it.

~~~py
requests.get('https://jsonplaceholder.typicode.com/posts')
assert {
    'json_schema': {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "body": {"type": "string"},
                "id": {"type": "number"},
                "title": {"type": "string"},
                "userId": {"type": "string"}
            }
        }
    }
}
~~~

The test runner was built for convenience:

- requests and assertions can be defined over multiple lines
- requests and assertions can use env vars
- requests without corresponding assertions are ignored
- the order of requests is preserved in the results tab

Assertions can be inserted seamlessly into a requester file; if you're not doing a test run they're simply ignored.


### Chaining Requests
If you need to run requests or tests one after another, in the order in which they're defined in your requester file, look for __Requester: Run Requests Serially__ or __Requester: Run Tests Serially__ in the command palette.

Behind the scenes, this just passes the `concurrency=1` arg to `requester` or `requester_run_tests`, and voilà, you've chained your requests.

Note: code inside your __env block/env file__ is always run serially, which includes any requests you put in there.


#### Chaining By Reference
If you need __true__ request chaining, such that a request can reference the `Response` object returned by the previous request, that's easy too. Requester lets you reference the most recently returned response using the `Response` variable. Copy the following code to a new view, highlight it, and run __Requester: Run Requests Serially__.

~~~py
get('http://httpbin.org/get')

get('http://httpbin.org/cookies', cookies={'url': Response.json()['url']})
~~~

If you don't run requests serially, this probably won't work, because requests are executed in parallel. All the requests may have already been executed before any of the responses return, which means none of them will be able to reference the `Response` object.


## Commands
Commands defined by this package, in case you want to change key bindings.

- __requester__
- __requester_replay_request__
- __requester_cancel_requests__: cancel all outstanding requests
- __requester_history__: search and re-execute past requests
- __requester_close_response_tabs__
- __requester_run_tests__
- __requester_show_tutorial__
- __requester_show_documentation__
- __requester_show_syntax__
- __requester_reorder_response_tabs__: reorders response tabs to match order of requests in requester file
- __requester_new_requester_file__: create empty requester file
- __requester_cancel_downloads__: cancel outstanding file downloads


## Settings
- __timeout__: default timeout in seconds for all requests
  + if you want to change this for a single request, __do so directly in the response tab__, not in your requester file
- __timeout_env__: default timeout in seconds for executing env block/env file
- __change_focus_after_request__: if a single request is executed, change focus to response tab after request returns
- __change_focus_after_requests__: if multiple requests are executed, change focus to final response tab after requests return
- __reorder_tabs_after_requests__: if multiple requests are executed, automatically reorder response tabs based on requests in requester file after requests return
- __history_file__: name of request history file, this is stored in User directory
- __history_max_entries__: max number of requests in history file
- __chunk_size__: chunk size for file downloads (bytes)
- __only_download_for_200__: only perform file download if response status code is 200


## Gotchas
Requester automatically includes the `timeout` argument in requests executed from your requester file. If you include this arg in your requests, __Requester will raise a SyntaxError__.

Not recommended: if you really want to disable automatic `timeout` for requests, set it to `None` in your Requester settings.

That's it.


## Contributing and Tests
I would be very grateful! [See here](https://github.com/kylebebak/Requester/blob/master/docs/contributing.md).


## Why Requester?
Requester combines features from applications like Postman, Paw, Insomnia and HTTPie with the elegance and power of Requests.

Requester leans on Requests as much as possible. This means Requester does most anything Requests does, which means it does most anything you need to explore, debug, and test a modern API.

It also means Requester uses an extensively documented, battle-tested library famed for its beauty. If you don't know how to do something with Requester, there are thousands of blog posts, articles and answers on Stack Overflow that explain how to do it.

Apart from being feature-rich, Requester is built for speed and simplicity. I was a Postman user before writing Requester, and I got tired of, for example, having to click in 4 places to add or change an env var. With Requester you might have to move your cursor up a few lines.

The paid collaboration features of HTTP client apps, such as sharing and versioning, are not only free in Requester, they're better. Requester works with text files, and as good as the developers at Postman and Paw are, they won't beat GitHub at collaboration, and they won't beat Git at version control.

Requester is cross-platform, free, and built for teams. If you debug web APIs for work or for fun, try it. Try it even if you don't use Sublime Text. You'll have to switch between two text editors, but you already have to switch between your editor and your HTTP client. Sublime Text running Requester probably has a smaller footprint than your HTTP client, and it's probably a lot easier to use =)
