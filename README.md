# Requester

![License](https://camo.githubusercontent.com/890acbdcb87868b382af9a4b1fac507b9659d9bf/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)

A simple and powerful HTTP client for Sublime Text 3, built on top of [Requests](http://docs.python-requests.org/en/master/). Like Requests, it's intuitive and easy to use.

Requester is like Postman for your text editor. Get environment variables, concurrent requests, multiple, editable response tabs and the elegant syntax of Requests, without neutering your keyboard.


## Features
- [Requests' syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + Easily set request body, query params, custom headers, cookies, use sessions...
- Environment variables, defined in requester file or in a separate env file
- Execute requests and display responses in parallel
- Edit and replay requests from individual response tabs
  + Automatically order response tabs
- Automatic syntax highlighting and pretty printing
- Clear error handling and error messages


## Installation
1. Install [Package Control](https://packagecontrol.io/) if you don't have it already.
2. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
3. Search for __Requester__ (not ~~Http Requester~~) and install it.
4. __If you're seeing errors__ every time you run a request, this probably means the __requests__ dependency wasn't installed successfully. To fix this, look for __Package Control: Satisfy Dependencies__ in the command palette, run it, and restart Sublime Text.


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

Now, go back to the requester file and use [multiple selection](https://www.sublimetext.com/docs/3/multiple_selection_with_the_keyboard.html) to select all 5 lines, and once again execute the requests.

Tabs will open for all 4 requests (Requester conveniently ignores the blank line). Before checking out these tabs, execute the requests yet again. You'll notice duplicate requests don't create a mess of new tabs, but simply overwrite the content in the matching response tabs.

Want to see something nifty? Mix up the order of the 4 open response tabs, come back to your requester file, and run __Requester: Reorder Response Tabs__.

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


#### Separate Env File
Requester also lets you save and source your env vars from a separate env file. To do this, first you want to save your requester file. This way you can use a __relative path__ from your requester file to your env vars file, which is convenient. Save it with any name, like `requester.py`.

Next, save a file with the name `requester_env.py` __in the same directory__ as `requester.py`, and add an env var to it.

~~~py
base_url = 'https://jsonplaceholder.typicode.com'
~~~

Finally, define the path of your `env_file` in your requester file like so:

~~~py
env_file = 'requester_env.py'

requests.get(base_url + '/albums')
requests.post(base_url + '/albums')
~~~

Requester will now look for the env file at the path `requester_env.py`, which is relative to the location of the requester file. You can change this path to any relative path you want, e.g. `relative/path/to/env.py`. You can also use an __absolute path__ to the env vars file if you want. Using an absolute path is necessary if you want to execute requests from a view which has never been saved.

#### Merging Vars from Env Block and Env File
Is totally fine. If a var has the same name in the env block and the env file, the var from the env block takes precedence.


### Request Body, Query Params, Custom Headers, Cookies
~~~py
get('http://httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/redirect-to?url=foo')
# response tab shows redirects
~~~

Body, Query Params, and Headers are passed to __requests__ as dictionaries. Cookies can be passed as a dict or an instance of `requests.cookies.RequestsCookieJar`. If you want to pass cookies in a jar instance, you need to instantiate it your env vars.

If you execute the last request, you'll notice the response tab shows the series of redirects followed by the browser.

If you don't know how to do something, check out __Requester: Show Tutorial__ from the command palette, or review syntax at the [Requests Quickstart](http://docs.python-requests.org/en/master/user/quickstart/).


### Sessions
~~~py
###env
import requests
s = requests.Session()
s.get('http://httpbin.org/cookies/set?session_id=12345', timeout=5)
###env

s.get('http://httpbin.org/get')
~~~

Need to log in first so all your requests include a session cookie? [Session objects](http://docs.python-requests.org/en/master/user/advanced/#session-objects) make this a cinch. 

Instantiate the session object in the env block and use it in your requests. Copy this code to a new file and give it a try.


## Commands
Commands defined by this package, in case you want to change key bindings.

- __requester__
- __requester_replay_request__
- __requester_close_response_tabs__
- __requester_show_tutorial__
- __requester_show_documentation__
- __requester_show_syntax__
- __requester_reorder_response_tabs__: reorders response tabs to match order of requests in requester file (doesn't work for requests that are defined over multiple lines)


## Settings
- __timeout__: default timeout in seconds for all requests
  + if you want to change this for a single request, __do so directly in the response tab__, not in your requester file
- __timeout_env__: default timeout in seconds for executing env block/env file
- __highlighting__: toggle automatic syntax highlighting
- __change_focus_after_request__: if a single request is executed, change focus to response tab after request returns
- __change_focus_after_requests__: if multiple requests are executed, change focus to final response tab after requests return
- __reorder_tabs_after_requests__: if multiple requests are executed, automatically reorder response tabs based on requests in requester file after requests return


## Gotchas
Requester automatically includes the `timeout` argument in requests executed from your requester file. If you include this arg in your requests, __Requester will raise a SyntaxError__.

Not recommended: if you really want to disable automatic `timeout` for requests, set it to `None` in your Requester settings.

Also, __don't include inline comments on the same lines__ as the requests in your requester file. For example, don't do this:

~~~py
requests.get('http://mysite.com/api') # comment on same line as request
~~~

Doing so can lead to unexpected results.

That's it.


## Contributing and Tests
[See here](https://github.com/kylebebak/Requester/blob/master/docs/contributing.md).


## Recap
There are several HTTP clients for Sublime Text, so why Requester? Because the others lack many of the following:

- Well-documented, intuitive syntax
- Environment variables
- Multiple, editable response tabs
- Automatic syntax highlighting

Postman addresses these concerns, which might be why it's so popular. But using an app like Postman has its own disadvantages:

- Constantly switching contexts between HTTP client and code.
- Manipulating requests requires lots of point and click: __keyboard wizardry is worthless__.
- Requests are stored in a proprietary format: difficult to share, difficult to add to version control.

Requester is built from the ground up to give you the best of both worlds. Try it, see for yourself =)
