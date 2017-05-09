# Requester
A simple and powerful HTTP client for Sublime Text 3, built on top of [Requests](http://docs.python-requests.org/en/master/). Like Requests, it's intuitive and easy to use.

Requester is like Postman for your text editor. Get environment variables, concurrent requests, multiple, editable response tabs and the elegant syntax of Requests, without neutering your keyboard.


## Features
- [Requests' syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + easily set request body, query params, custom headers, cookies...
- Environment variables
- Execute requests and display responses in parallel
- Edit and replay requests from individual response tabs
- Automatic syntax highlighting and pretty printing
- Clear error handling and error messages


## Installation
1. Install [Package Control](https://packagecontrol.io/) if you don't have it already.
2. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
3. Search for __Requester__ (not ~~Http Requester~~) and install it.


## Getting Started
Open a file and insert the following:
~~~py
requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

get('https://jsonplaceholder.typicode.com/posts')
post('https://jsonplaceholder.typicode.com/posts')
~~~

Place your cursor on one of the lines and hit <kbd>ctrl+r</kbd>. Or, look for __Requester: Run Requests__ in the command palette and hit Enter. A response tab will appear, with a name like __GET: /albums__.

Head to the response tab and check out the response. Hit <kbd>ctrl+r</kbd> or <kbd>cmd+r</kbd> to replay the request. You can edit the request, which is at the top of the file, before replaying it.

Now, go back to the requester file and use [multiple selection](https://www.sublimetext.com/docs/3/multiple_selection_with_the_keyboard.html) to select all 5 lines, and once again hit <kbd>ctrl+r</kbd>.

Tabs will open for all 4 requests (Requester conveniently ignores the blank line). Before leaving your requester file, hit <kbd>ctrl+r</kbd> yet again. Duplicate response tabs will close before reopening, so that you don't have multiple tabs for each request.

Prefixing your requests with __requests.__ is optional. If you want to close all open tabs, look for __Requester: Close All Response Tabs__ in the command palette.


### Environment Variables
It's time to add environment variables your requests. To do this, you first need to save your requester file. Save it with any name, like `requester.py`. Then modify it to use some environment variables.

~~~py
requests.get(base_url + '/albums')
requests.post(base_url + '/albums')

get(base_url + '/posts')
post(base_url + '/posts')
~~~

Next, save a file with the name `requester_env.py` __in the same directory__ as `requester.py`, and add an env var to it.

~~~py
base_url = 'https://jsonplaceholder.typicode.com'
~~~

When you run your requests, __Requester__ looks for a requester env file with the name `requester_env.py` in the same directory as the requester file. It includes the variables defined in this file with your requests.

If you want to change the name or location of the env file, simply define a new `env_file` in your requester file like so:

~~~py
env_file = 'relative/path/to/env.py'

requests.get(base_url + '/albums')
requests.post(base_url + '/albums')

get(base_url + '/posts')
post(base_url + '/posts')
~~~

Requester will now look for the env file at `relative/path/to/env.py`, which is relative to the location of the requester file.


### Request Body, Query Params, Custom Headers, Cookies
~~~py
get('http://httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})
get('http://httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})
get('http://httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})
get('http://httpbin.org/redirect-to?url=foo') # response tab shows redirects
~~~

Body, Query Params, and Headers are passed to __requests__ as dictionaries. Cookies can be passed as a dict or an instance of `requests.cookies.RequestsCookieJar`. If you want to pass cookies in this way, they must be instantiated in your env vars file.

If you execute the last request, you'll notice the response tab shows the series of redirects followed by the browser.

If you don't know how to do something, just have a look at the [Requests Quickstart](http://docs.python-requests.org/en/master/user/quickstart/).


## Commands
Commands defined by this package, in case you want to change key bindings.

- __requester__
- __requester_replay_request__
- __requester_close_response_tabs__


## Settings
- __env_file__: relative path from requester files to env files
  + this can be overridden by defining the `env_file` variable in an individual requester file
- __timeout__: default timeout in seconds for all requests
  + if you want to change this for a single request, __do so directly in the response tab__, not in your requester file


## Gotchas
Requester automatically includes the `timeout` argument in requests executed from your requester file. If you include this arg in your requests, __Requester will raise a SyntaxError__.

That's it.


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
