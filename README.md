# Requester: HTTP Client for Humans

[![Join the chat at https://gitter.im/kylebebak/Requester](https://badges.gitter.im/kylebebak/Requester.svg)](https://gitter.im/kylebebak/Requester?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

![License](https://camo.githubusercontent.com/890acbdcb87868b382af9a4b1fac507b9659d9bf/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)
[![Build Status](https://travis-ci.org/kylebebak/Requester.svg?branch=master)](https://travis-ci.org/kylebebak/Requester)
[![Coverage Status](https://coveralls.io/repos/github/kylebebak/Requester/badge.svg?branch=master)](https://coveralls.io/github/kylebebak/Requester?branch=master)


__Requester__ is a modern, team-oriented HTTP client for Sublime Text 3 that combines features of apps like Postman, Paw and HTTPie with rock-solid usability and the secret sauce of Requests. 🌟

- [Super classy, well-documented syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + Easily set request body, query params, custom headers, cookies
  + Support for sessions, authentication
  + Forms and file uploads, Wget-style downloads  
  + HTTPS, proxies, redirects, and more
- Intuitive, modern UX
  + Define [__environment variables__](#environment-variables) with regular Python code
  + Execute requests and display responses in parallel, [__or chain requests__](#chaining-by-reference)
  + Edit and replay requests from individual response tabs, page through past requests
    * [Explore hyperlinked APIs](#explore-hyperlinked-apis-hateoas) from response tabs
  + Fuzzy search [request navigation and request history](#navigation-and-history)
  + Formatted, colorized output with automatic syntax highlighting
  + Clear error handling and error messages
- Perfect for teams
  + Version and share requests however you want (Git, GitHub, etc)
  + Export requests to cURL or HTTPie, import requests from cURL
  + Lightweight, integrated test runner with support for JSON Schema
    * [__Export Requester tests to a runnable test script__](#export-tests-to-runnable-script)
  + [AB-style](https://httpd.apache.org/docs/2.4/programs/ab.html) benchmarking tool
  + Runs on Linux, Windows and macOS/OS X

---

If you're looking for an HTTP client you should try Requester __even if you've never used Sublime Text__. [Here's why](#why-requester).


## Contents
- [Installation](#installation)
- [Getting Started](#getting-started)
  + [Jump to Request](#jump-to-request)
  + [Multiline Requests](#multiline-requests)
  + [JSON Response Formatting](#json-response-formatting)
  + [Ergonomic GET Requests](#ergonomic-get-requests)
  + [Pinned Response Tabs](#pinned-response-tabs)
  + [Environment Variables](#environment-variables)
- [Advanced Features](#advanced-features)
  + [Separate Env File](#separate-env-file)
    * [Merging Vars from Env Block and Env File](#merging-vars-from-env-block-and-env-file)
  + [Request Body, Query Params, Custom Headers, Cookies](#request-body-query-params-custom-headers-cookies)
  + [Sessions](#sessions)
  + [Authentication](#authentication)
  + [Forms and File Uploads](#forms-and-file-uploads)
  + [Downloads](#downloads)
    * [Downloaded File Name](#downloaded-file-name)
  + [Cancel Outstanding Requests](#cancel-outstanding-requests)
  + [Chaining Requests](#chaining-requests)
    * [Chaining by Reference](#chaining-by-reference)
- [Navigation and History](#navigation-and-history)
  + [Requester File Navigation (.pyr extension)](#requester-file-navigation-pyr-extension)
  + [Request History](#request-history)
    * [Page Through Past Requests](#page-through-past-requests)
  + [Explore Hyperlinked APIs (HATEOAS)](#explore-hyperlinked-apis-hateoas)
  + [Options Requests](#options-requests)
- [Import Any Python Package with Requester](#import-any-python-package-with-requester)
  + [Pip3 Quickstart](#pip3-quickstart)
  + [OAuth1 and OAuth2](#oauth1-and-oauth2)
- [Test Runner](#test-runner)
  + [Making Assertions About Response Structure](#making-assertions-about-response-structure)
  + [Export Tests to Runnable Script](#export-tests-to-runnable-script)
- [Benchmarking Tool](#benchmarking-tool)
- [Export/Import with cURL, HTTPie](#exportimport-with-curl-httpie)
- [Special Keyword Arguments](#special-keyword-arguments)
- [Commands](#commands)
- [Response Tab Commands](#response-tab-commands)
- [Settings](#settings)
- [Contributing and Tests](#contributing-and-tests)
- [Inspired By](#inspired-by)
- [Why Requester?](#why-requester)


## Installation
1. Download and install [Sublime Text 3](https://www.sublimetext.com/3).
2. Install [Package Control for Sublime Text](https://packagecontrol.io/).
3. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
4. Search for __Requester__ (not ~~Http Requester~~) and install it.
5. __If you're seeing errors__ every time you run a request, this probably means the __requests__ dependency wasn't installed successfully. To fix this, look for __Package Control: Satisfy Dependencies__ in the command palette, run it, and restart Sublime Text.


## Getting Started
Open the interactive tutorial in Sublime Text! Look for __Requester: Show Tutorial__ in the command palette. Alternatively, just keep reading.

Open a file and insert the following.

~~~py
requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

get('https://jsonplaceholder.typicode.com/posts')  # 'requests.' prefix is optional
post('jsonplaceholder.typicode.com/posts')  # as is the URL scheme
~~~

Place your cursor on one of the lines and hit <kbd>ctrl+alt+r</kbd> (<kbd>ctrl+r</kbd> on macOS). Or, look for __Requester: Run Requests__ in the command palette <kbd>shift+cmd+p</kbd> and hit Enter. A response tab will appear, with a name like __GET: /albums__.

Head to the response tab and check out the response. Hit <kbd>ctrl+alt+r</kbd> or <kbd>ctrl+r</kbd> (<kbd>ctrl+r</kbd> or <kbd>cmd+r</kbd> on macOS) to replay the request. You can edit the request, which is at the top of the file, before replaying it.

Now, go back to the requester file and highlight all 5 lines, and once again execute the requests.

Tabs will open for all 4 requests (Requester conveniently ignores the blank line). Before checking out these tabs, execute the requests yet again. You'll notice duplicate requests don't create a mess of new tabs, they just overwrite the content in the matching response tabs (read on if you'd like to change this behavior).


### Jump to Request
Go back to your Requester file and save it as `<anything>.pyr`. The extension is important. Run Sublime Text's __Goto Symbol__ by pressing <kbd>ctrl+r</kbd> (<kbd>cmd+r</kbd> on macOS). If your Requester file has this extension, you can jump between your requests almost instantaneously.


### Multiline Requests
For executing requests defined over multiple lines, you have two options:

- fully highlight one or more requests and execute them
- place your cursor on the __first line__ of a request and execute it

~~~py
get(
    'https://jsonplaceholder.typicode.com/posts'
)
post(
    'jsonplaceholder.typicode.com/posts'
)
~~~

Notice that if a URL scheme isn't supplied, Requester sets it as `http` by default.

If you want to close all open tabs, look for __Requester: Close All Response Tabs__ in the command palette.


### JSON Response Formatting
Requester supports 3 options for JSON response formatting, `indent_sort`, `indent`, and `raw`. The default value for all requests, which can be changed in Requester's settings, is `indent_sort`. If you don't want keys in objects sorted alphabetically, use `indent` or `raw`.

~~~py
get('http://headers.jsontest.com/', fmt='indent_sort')
get('http://headers.jsontest.com/', fmt='indent')
get('http://headers.jsontest.com/', fmt='raw')
~~~


### Ergonomic GET Requests
Try sending the following requests. This is obviously not valid Python syntax, but Requester has a shortuct for basic GET requets. If you run Requester on a URL like the one below, it automatically wraps it like so: `requests.get('<url>')`. And it doesn't wrap the URL in quotes if it's already got them.

~~~py
httpbin.com/get
'httpbin.com/headers'
~~~


### Pinned Response Tabs
When you execute a request, Requester overwrites response tabs that have the same request method and URL as the request you're executing. If you want multiple views into the same request, you can __pin__ your response tabs. Pinned response tabs are never overwritten.

In a response tab, go to the command palette and look for __Requester: Pin/Unpin Response Tab__, or look in the response tab for the keyboard shortcut to __pin/unpin tab__.


### Environment Variables
It's time to refactor your requests to use environment variables. Requester has a powerful scripting language for env vars... Python!

You can define them directly in your requester file. Just put your variables in a code block fenced by __###env__ lines. Try executing these requests.

~~~py
###env
base_url = 'https://jsonplaceholder.typicode.com'
###env

get(base_url + '/albums')
post(base_url + '/albums')
~~~

Variables you define in your env block can be referenced by any of your requests. The __###env__ lines must have no leading or trailing spaces. Only the first env block in a requester file is used.

You can import and use anything in Python's standard library in your env block. You can also import and use `requests`. This makes Requester's env vars __powerful and flexible__. Here's a toy example. Copy it to another file and give it a try.

~~~py
###env
import requests
base_url = 'https://www.metaweather.com/api'
r = requests.get(base_url + '/location/search/?lattlong=19.4326,-99.1332')
woeid = str(r.json()[0]['woeid'])  # get "where on earth id" for Mexico City
###env

get('{}/location/{}/'.format(base_url, woeid))  # use "where on earth id" to get Mexico City's weather data
~~~


## Advanced Features
Find out what makes Requester really special. In the future if you need to refresh your memory, just press <kbd>shift+cmd+p</kbd> to open the command palette, and type __Requester__.


### Separate Env File
Requester can save and source your env vars from a separate env file. To do this, first you want to save your requester file. This way you can use a __relative path__ from your requester file to your env file, which is convenient. Save it with any name, but use the `.pyr` extension. `requester.pyr` is fine. More on the `.pyr` extension later.

Next, save a file with the name `requester_env.py` in the same directory as `requester.pyr`, and add an env var to it.

~~~py
base_url = 'https://jsonplaceholder.typicode.com'
~~~

Finally, define the path of your `env_file` in your requester file like so:

~~~py
env_file = 'requester_env.py'

get(base_url + '/albums')
post(base_url + '/albums')
~~~

Requester will now look for the env file at the path `requester_env.py`, which is relative to the location of the requester file. You can change this path to any relative path you want, e.g. `relative/path/to/env.py`. You can also use an __absolute path__ to the env vars file if you want.


#### Merging Vars from Env Block and Env File
Is totally fine. If a var has the same name in the env block and the env file, the var from the env file takes precedence.

Why? If you're working on a team, your requester file should probably be in version control. Static env vars and default values for dynamic env vars can be defined in the env block of your requester file.

Dynamic env vars, like a `base_url` that might point to staging one minute and production the next, can be (re)defined in an env file. Put the env file in your `.gitignore`. This way devs can tweak their envs without making useless commits or stepping on each other's toes.


### Request Body, Query Params, Custom Headers, Cookies
~~~py
post('httpbin.org/post', data={'key1': 'value1', 'key2': 'value2'})

post('httpbin.org/post', json=[1, 2, 3])
post('httpbin.org/post', json={'name': 'Jimbo', 'age': 35, 'married': False, 'hobbies': ['wiki', 'pedia']})

get('httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/redirect-to?url=foo')  # response tab shows redirects
~~~

Body, Query Params, and Headers are passed to __requests__ as dictionaries. Cookies can be passed as a dict or an instance of `requests.cookies.RequestsCookieJar`.

If you execute the last request, you'll notice the response tab shows the series of redirects followed by the browser.

>If you want to disallow redirects by default, simply change Requester's `allow_redirects` setting to `false`.


### Sessions
Need to log in first so all your requests include a session cookie? [Session objects](http://docs.python-requests.org/en/master/user/advanced/#session-objects) make this a cinch. 

Instantiate the session object in the env block and use it in your requests. Copy this code to a new file, run the request, and check out the `session_id` cookie in the request headers.

~~~py
###env
import requests
s = requests.Session()
s.get('http://httpbin.org/cookies/set?session_id=12345', timeout=5)
###env

s.get('http://httpbin.org/get')
s.get('http://httpbin.org/cookies/set?token=789')
~~~

In the example above, each time you execute __Requester: Run Requests__, a new session is created, and once all responses are returned the session is destroyed.

If you highlight and run multiple requests that depend a session `s`, they will all share the same session `s`. If you run them serially, you can control the order in which cookies are added to the session.


### Authentication
Requests has [excellent support for authentication](http://docs.python-requests.org/en/master/user/authentication/). __Basic Authentication__ and __Digest Authentication__ are built in, and implementing custom auth schemes is easy.

To use a custom auth scheme with Requester you define the auth class in your env block or env file, then pass an instance of this class to the `auth` argument of a request.

Requester comes with a few pre-written auth classes you can use in your code, or as a reference. Run __Requester: Authentication Options__ in the command palette to see the list. Have a look at __Token__ auth, which simplifies passing a token in the __"Authorization"__ header of your requests.

>If you want help handling more complicated forms of auth, like OAuth1 and OAuth2, have a look [at this section](#import-any-python-package-with-requester).


### Forms and File Uploads
Requests makes posting forms and uploading files easy. See how in the Requests documentation.

- [Forms](http://docs.python-requests.org/en/latest/user/quickstart/#more-complicated-post-requests)
- [File uploads](http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file)
- [Multiple file uploads](http://docs.python-requests.org/en/master/user/advanced/#post-multiple-multipart-encoded-files)

Requests also supports streaming and chunked file uploads, which is great (and necessary) if the file you're uploading doesn't fit in memory, but the API is a bit more complicated. Requester has the special `streamed` and `chunked` arguments to make these uploads trivial.

~~~py
post('https://requestb.in/<your_request_bin>', streamed='/path/to/file')
post('https://requestb.in/<your_request_bin>', chunked='/path/to/file')
~~~

If you pass the file as a `chunked` upload, the __"Transfer-Encoding": "chunked"__ header is added to your request. Some servers don't allow chunked uploads, in which case you can use a `streamed` upload. If they're an option, chunked uploads are nicer: they come with a progress bar and can be cancelled.

>If you need streaming uploads for multipart forms, or uploads of multiple files, the `requests-toolbelt` packages has your back. Check out [this section](#import-any-python-package-with-requester).


### Downloads
Requester also provides Wget-style downloads. Just add the `filename` keyword arg to a call to `requests.get`.

~~~py
get('http://www.nationalgeographic.com/content/dam/animals/thumbs/rights-exempt/mammals/d/domestic-dog_thumb.jpg', filename='image.jpg')
~~~

As with streamed and chunked uploads, `filename` can be an absolute path, or a path relative to your requester file. Also, as with uploads, __multiple downloads can be executed in parallel__. Downloads can be cancelled. They come with a nice progress bar.


#### Downloaded File Name
If you pass a value for `filename` that has no __basename__, Requester infers the name of the file from the URL. Examples of such `filename`s: __''__, __relative/path/__, __/absolute/path/__.

In this mode, if the file name already exists, Requester adds a suffix to make the file name unique. Try downloading this file several times in succession.

~~~py
get('http://www.nationalgeographic.com/content/dam/animals/thumbs/rights-exempt/mammals/d/domestic-dog_thumb.jpg', filename='')
~~~


### Cancel Outstanding Requests
If you have outstanding requests that are taking a while to return, and you don't want to wait for them to time out, you can cancel them by calling __Requester: Cancel Requests__ from the command palette.


### Chaining Requests
If you need to run requests or tests one after another, in the order in which they're defined in your requester file, look for __Requester: Run Requests Serially__ or __Requester: Run Tests Serially__ in the command palette.

Behind the scenes, this just passes the `concurrency=1` arg to `requester` or `requester_run_tests`, and voilà, you've chained your requests.

>Note: code inside your __env block/env file__ always runs serially, which includes any requests you put in there.


#### Chaining by Reference
If you need __true__ request chaining, such that a request can reference the `Response` object returned by the previous request, that's easy too. Requester lets you reference the most recently returned response using the `Response` variable, and also lets you __name__ your responses. Copy the following code to a new view, highlight it, and run __Requester: Run Requests Serially__.

~~~py
get('http://httpbin.org/get')

get('http://httpbin.org/cookies', cookies={'url': Response.json()['url']})
~~~

If you don't run requests serially, the second request fails, because it's executed before the first request returns. Now try __naming__ the response from a request using the `name` argument.

~~~py
get('httpbin.org/get', name='first_response')
get('google.com', allow_redirects=False)
get('httpbin.org/cookies', cookies={'url': first_response.json()['url']})
~~~

>By the way, you shouldn't name an env var "Response", or with the same name that you pass to a request's `name` argument, because it will be overwritten.


## Navigation and History
UX is sort of an obsession for me, and it's sacred in Requester. The biggest UX difference between Requester and other HTTP clients is the ease with which you can find, modify and execute your requests — the ones in your Requester file, and the ones in you request history.


### Requester File Navigation (.pyr extension)
Try running __Requester: New Requester File__ from the command palette. You'll get a file pointing to an empty env file, with an empty env block, and a link to Requester's syntax at the top. It's ready for starting a new collection of requests.

You'll notice the file you just created has a special extension, `.pyr`. This is the Python Requester extension. __You should save all your Requester files with this extension__.

Here's why. Run __Requester: New Requester File (Navigation Demo)__ from the command palette. You'll get a new requester file with some stub requests already inserted. Now, run Sublime's __Goto Symbol__ command (<kbd>cmd+r</kbd> on macOS)... You can jump between request groups and individual requests almost instantaneously using fuzzy search!

Behind the scenes, `.pyr` files get the special __Requester__ syntax applied to them (you can set this syntax on any view you like by running __Set Syntax: Requester__ from the command palette). __Requester__ is the default Python syntax with a few Requester-specific improvements:

- your `###env` block delimeters are highlighted
- request groups can be declared by starting a line with two or more `##` characters
- you can use Sublime's __Goto Symbol__ to jump between requests and request groups ✨✨


### Request History
Requester saves a history of executed requests. Call __Requester: Request History__ to check it out. They appear in reverse chronological order and include each request's age, URL, response status code, and requester file. They're fuzzy searchable!

Choose an old request and select it. A special response tab will open, with the request string, some response metadata, and the usual response tab commands, but nothing else.

Replay the chosen request. It runs as if it were executed from its original requester file, but it also pulls in up-to-date env vars from the env block and the env file.


#### Page Through Past Requests
Notice the key bindings for __prev/next request__ in response tabs? Give them a try.

>If these or other bindings don't work, don't fret! Here's a 1 minute, [permanent fix to the problem](#response-tab-commands).

These commands let you page through past requests one at a time, and can be used from any response tab. __Combine them with fuzzy search for request searching nirvana__.

Imagine you want to find a GET request you ran when you were working with the Twitter API over the weekend. You open search with __Requester: Request History__ and type _twitter_, and see a bunch of requests from around 3 days ago. You're not sure which is the right one, so you hit enter to get a better look.

From here, you begin to page back, past a few 40Xs, some POSTs, then boom, the elusive 200 GET is right in front of you. You replay it, and now it's back on top of your request history. Next time you want it it'll take 1 second to find instead of 10.

---

Requester's history is one of Requester's most convenient features, which means you might want to modify your keymap and bind something to __requester_history__. ✨✨

Open your keymap from the command palette by running __Preferences: Key Bindings__. For example, on macOS you might bind it to <kbd>ctrl+h</kbd> by adding the following:

~~~json
{ "keys": ["ctrl+h"], "command": "requester_history" },
~~~


### Explore Hyperlinked APIs (HATEOAS)
Ever used an API that returns __hyperlinks__ to other resources in the response? This pattern is part of a larger concept in REST called HATEOAS, or [hypermedia as the engine of application state](http://www.django-rest-framework.org/topics/rest-hypermedia-hateoas/). 

It's a mouthful, but the idea is simple: an API response should tell clients how to interact with related resources by providing them hyperlinks to those resources. This allows APIs to change without breaking clients, as long as clients are written to take their cues from the hyperlinks returned by the API.

__Requester is ready-made for exploring these APIs__. From a response tab, highlight any URL and press <kbd>ctrl+e</kbd> (<kbd>cmd+e</kbd> on macOS). Instead of replaying the original request, Requester sends a GET request to the highlighted URL and opens the response in a new tab.

It also compares the domain of the highlighted URL with the domain of the original request. If they're the same, Requester __includes the same args and kwargs in the new request__. If the original request was authenticated, the "exploratory" request will be authenticated as well.

If the domains are not the same, Requester strips all additional args and kwargs from the request, to ensure that none of your auth credentials are sent to a URL not belonging to the "source" API.

~~~py
post('httpbin.org/post',
    headers={'Authorization': 'Bearer my_secret_token'},
    json={'same_domain': 'http://httpbin.org/get', 'other_domain': 'https://jsonplaceholder.typicode.com/posts'}
)
~~~

Execute the request above. In the response tab, try highlighting each of the URLs in the response body and sending exploratory requests. Requester makes it trivial to explore hyperlinked URLs without worrying about leaking your credentials. ✨✨


### Options Requests
Want to see which HTTP verbs a given endpoint accepts? Send an `OPTIONS` request to the endpoint. Requester makes this ridiculously easy -- from a response tab, just press <kbd>ctrl+o</kbd> (<kbd>cmd+o</kbd> on macOS).


## Import Any Python Package with Requester
Requester comes bundled with the `requests` and `jsonschema` packages, but you can trivially extend it to source __any__ Python 3 package in its env. All you have to do is set Requester's `packages_path` setting to a directory with Python 3 packages. Requester can then import these packages in your env block or env file. ✨✨

In my settings for Requester `packages_path` points to a Python 3 virtual env: `/Users/kylebebak/.virtualenvs/general/lib/python3.5/site-packages`. I use `pip` to install these packages.

Here are a couple of no-brainers:

- [requests-oauthlib](https://github.com/requests/requests-oauthlib)
- [requests-toolbelt](https://github.com/requests/toolbelt)


### Pip3 Quickstart
If you don't have `virtualenv` or you're not comfortable using it, the quick solution is to install Python 3, which will install `pip3` and `python3` executables. Run `which pip3` to make sure you've done this.

Then run `pip3 install requests-oauthlib`, `pip3 install requests-toolbelt`, and so on for whatever packages you'd like to use with Requester.

Finally, run `pip3 show requests-oauthlib`, and look for the __LOCATION__ field in the output. Now you know where pip is installing your packages.

Use this path as your `packages_path` setting in Requester's settings file. To open these settings, look for __Requester: Settings__ in the command palette.


### OAuth1 and OAuth2
__requests-oauthlib__ makes OAuth1 and OAuth2 a lot easier. Let's say you want explore the Twitter REST API, which uses OAuth1 for authentication. Go to <https://apps.twitter.com/app/new>, create a new application, then go to the __Keys and Access Tokens__ tab for your application. Generate an access token and an access token secret, grab your API key and secret, and pass them to `OAuth1`.

~~~py
###env
from requests_oauthlib import OAuth1
auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
###env

get('https://api.twitter.com/1.1/statuses/user_timeline.json?screen_name=stackoverflow&count=100', auth=auth)

# ...
#   "created_at": "Wed Sep 13 19:10:10 +0000 2017",
#   "entities": {
#     "hashtags": [],
#     "symbols": [],
#     "urls": [
#       {
#         "display_url": "stackoverflow.blog/2017/09/06/inc\u2026",
#         "expanded_url": "https://stackoverflow.blog/2017/09/06/incredible-growth-python/",
#         "indices": [
#           32,
#           55
#         ],
#         "url": "https://t.co/4NCaBp5RKh"
#       }
#     ],
#     "user_mentions": []
#   },
#   "favorite_count": 2,
# ...
~~~

Python has auth libraries for authenticating with a wide variety of APIs. With `pip` and the `packages_path` setting Requester can access them all.


## Test Runner
Requester has a built-in test runner! Copy and paste this into an empty file.

~~~py
###env
base_url = 'https://jsonplaceholder.typicode.com'
prop = 'status_code'
###env

# first request
get(base_url + '/posts')
assert {prop: 200, 'encoding': 'utf-8'}

# second request, with no assertion
get(base_url + '/profile')

# third request
get(base_url + '/comments')
assert {'status_code': 500}
~~~

Highlight all the requests, look for __Requester: Run Tests__ in the command palette, and run it. You'll notice that test results are displayed for the first and third requests.

What's going on here? If a request has an assertion below it, the `key, value` pair in the assertion is compared with the returned `Response` object. If `key` is a valid property of the `Response` object, `value` is compared with the property. If they're not equal discrepancies are displayed.

Some valid properties: `apparent_encoding`, `cookies`, `encoding`, `headers`, `history`, `is_permanent_redirect`, `is_redirect`, `json`, `links`, `reason`, `status_code`, `text`, `content`.


### Making Assertions About Response Structure
`cookies`, `headers` and `json` point to Python dicts or lists, which means comparing for equality isn't very useful. Much more useful are the following special assertion keys for these properties: `cookies_schema`, `headers_schema`, `json_schema`.

Including one of these in an assertion will validate the corresponding property with [jsonschema.validate](https://github.com/Julian/jsonschema). __This lets you describe the structure of cookies, headers, and JSON responses returned by your API__. Look at the example below. The test fails because we assert that the `userId` for each object in the array of results has a type of `string`, and this isn't true.

If you have a JSON API, [JSON Schema](http://json-schema.org/) is an excellent way to describe your API's data format. Use it.

~~~py
get('https://jsonplaceholder.typicode.com/posts')
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

- requests and assertions can use env vars
- requests without corresponding assertions are ignored
- the order of requests is preserved in the results tab

Assertions can be inserted seamlessly into a requester file; if you're not doing a test run they're simply ignored.


### Export Tests to Runnable Script
If you want to integrate your Requester tests into your app's test routine, Requester can export request/assertion pairs to a runnable test script. Highlight the requests and assertions you want to export and look for __Requester: Export Tests To Runnable Script__ in the command palette.

This test script depends only on the Python `requests` and `jsonschema` packages. To run it from the command line you just call `python -m unittest <test_module_name>`. The default test module name is __requester_tests__.

The test export command lacks two conveniences available to all other Requester commands:

- it doesn't automatically include the timeout argument in calls to `requests`
- it doesn't automatically add a scheme to URLs with no scheme


## Benchmarking Tool
Want to see how your staging or production servers hold up under load? Requester's benchmarking tool is like [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) or [siege](https://www.joedog.org/siege-home/), but it's easier to use. Highlight one or more requests, and call __Requester: Run Benchmarks__ from the command palette.

You'll be prompted for the number `N` of each request to run, and the concurrency `C`. In other words, if you highlight 5 requests, then input 100 for `N` and 20 for `C`, you'll send a total of 500 requests, 100 to each endpoint, in bunches of 20 at a time.

Requester then displays a profile with response time metrics, grouped by request method and URL. Try it on these 3 here, with N=100 and C=20.

~~~py
get('http://httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})
~~~

It goes without saying, but please don't use this for DoS attacks on servers you don't own. Regardless of what you pass for `N`, the total number of requests executed is capped at 100000. `C` is capped at 1000, which translates to [tens of millions of requests per day](https://serverfault.com/questions/274253/apache-ab-choosing-number-of-concurrent-connections).

>Warning: benchmarks runs with `C` above ~100 may slow down the UI while they are running.


## Export/Import with cURL, HTTPie
Need your requests in a more portable format? Requester exports to and import from the ubiquitous [cURL](https://curl.haxx.se/) format.

This makes it trivial to share requests with teammates who don't use Requester, or execute your requests on any server you like.

Prefer [HTTPie](https://httpie.org/) instead of cURL? You can also export requests to HTTPie!

Exporting works seamlessly with env vars. Just highlight a group of requests and look for __Requester: Export To cURL__ or __Requester: Export To HTTPie__ in the command palette. For importing it's __Requester: Import From cURL__. Exporting to HTTPie supports a bunch of features, including basic and digest authentication, file downloads, and even sessions. For sessions, just highlight your env block along with the requests you want to export.


## Special Keyword Arguments
Requester's syntax is basically identical to Requests' syntax, but it adds support for the following special `kwargs`.

- __fmt__: one of ('raw', 'indent', 'indent_sort'), controls formatting of JSON responses
- __name__: binds name to response object so that it can be referenced by subsequent serially executed requests
- __filename__: downloads the response to the specied path
- __streamed__: performs a streaming upload of the specified file
- __chunked__: performs a chunked upload, with a progress indicator, of the specified file


## Commands
Commands defined by this package, in case you want to add or change key bindings.

- __requester__
- __requester_replay_request__
- __requester_explore_url__: explore url in response tab
- __requester_history__: search and re-execute past requests
- __requester_cancel_requests__: cancel all outstanding requests
- __requester_cancel_downloads__: cancel outstanding file downloads
- __requester_cancel_uploads__: cancel outstanding file uploads
- __requester_response_tab_toggle_pinned__: pin (or unpin) a response tab so that it isn't overwritten by requests with its same method and URL
- __requester_close_response_tabs__
- __requester_reorder_response_tabs__: reorders response tabs to match order of requests in requester file
- __requester_new_requester_file__: create empty requester file
- __requester_run_tests__
- __requester_export_tests__: export tests to runnable script
- __requester_prompt_benchmarks__
- __requester_auth_options__
- __requester_export_to_curl__: export selected requests to cURL
- __requester_export_to_httpie__: export selected requests to HTTPie
- __requester_import_from_curl__: import selected cURL requests
- __requester_show_tutorial__
- __requester_show_documentation__
- __requester_show_syntax__


## Response Tab Commands
The following commands are only available in response tabs. The key bindings listed below are for macOS. Every response tab shows these key bindings.

- __cmd+r__: replay request
- __ctrl+alt+ ←/→__: prev/next request
- __cmd+t__: pin/unpin tab
- __cmd+e__: explore URL
- __cmd+o__: options

If you try to execute one of these commands and nothing happens, you've already mapped the binding to another command. Run __Preferences: Key Bindings__ from the command palette, find the conflicting key combination, add the following `context` to the binding, and restart Sublime Text.

~~~json
"context": [
  { "key": "setting.requester.response_view", "operator": "equal", "operand": false }
]
~~~

This removes the conflict by disabling your binding __only__ in Requester's response views.


## Settings
Requester's modifiable settings, and their default values. You can override any of these settings by creating a `Requester.sublime-settings` file in Sublime's `Packages/User` directory. The easiest way to do this is go to __Preferences > Package Settings > Requester > Settings__ from the menu bar, or look for __Requester: Settings__ in the command palette.

- __timeout__, `15`: default timeout in seconds for all requests
- __timeout_env__, `15`: default timeout in seconds for executing env block/env file
- __allow_redirects__, `true`: are redirects allowed by default?
- __scheme__, `"http"`: scheme prepended to URLs in case no scheme is specified
- __fmt__, `"indent_sort"`: JSON response formatting, one of ("raw", "indent", "indent_sort")
- __max_content_length_kb__, `5000`: don't render responses whose content length (kilobytes) exceeds this value
- __change_focus_after_request__, `true`: if a single request is executed, change focus to response tab after request returns
- __reorder_tabs_after_requests__, `false`: if multiple requests are executed, automatically reorder response tabs based on requests in requester file after requests return
- __pin_tabs_by_default__, `false`: pin newly opened response tabs by default, so they aren't overwritten by requests with the same method and URL
- __history_file__, `"Requester.history.json"`: name of request history file, stored in User directory
- __history_max_entries__, `250`: max number of requests in history file
- __chunk_size__, `1024`: chunk size for file downloads (bytes)
- __only_download_for_200__, `true`: only perform file download if response status code is 200
- __packages_path__, `""`: absolute path to extra python packages included in env


## Contributing and Tests
[See here](https://github.com/kylebebak/Requester/blob/master/docs/_content/contributing.md).


## Inspired By
- [Requests](http://docs.python-requests.org/en/master/) — Requester sends all its requests using this amazing library.
- [HTTPie](https://github.com/jakubroztocil/httpie) — A truly "Pythonic" tool. Its focus on intuitiveness and ergonomics inspired many of Requester's features, including its [docs site](http://requester.org).
- [Postman](https://www.getpostman.com/) — A strong influence on much of Requester's "managed" UI.


## Why Requester?
Requester combines features from applications like Postman, Paw, Insomnia and HTTPie with the elegance and power of Requests and rock-solid UX of Sublime Text.

Requester leans on [Requests](http://docs.python-requests.org/en/master/user/quickstart/) as much as possible. This means Requester does most anything Requests does, which means it does most anything you need to explore, debug, and test a modern API.

It also means Requester uses an extensively documented, battle-tested library famed for its beauty. If you don't know how to do something with Requester, there are thousands of blog posts, articles and answers on Stack Overflow that explain how to do it.

Apart from being feature-rich, __Requester is built for speed and simplicity__. I was a Postman user before writing Requester, and I got tired of, for example, having to click in 4 places to add or change an env var. With Requester you might have to move your cursor up a few lines.

Request navigation and history are especially powerful. Finding a request you executed a week ago, editing it and executing it is lightning fast.


[![Requester](https://raw.githubusercontent.com/kylebebak/Requester/master/assets/requester.png)](https://www.youtube.com/watch?v=kVO5AWIsmF0 "Requester")


The paid collaboration features of HTTP client apps, such as sharing and versioning, are not only free in Requester, they're better. Requester works with text files, and as good as the developers at Postman and Paw are, they don't beat GitHub at collaboration, and they don't beat Git at version control.

Need to share requests with someone who doesn't use Requester? Exporting all of your requests to cURL or HTTPie takes a few seconds.

Requester is cross-platform and built for teams. If you debug web APIs for work or for fun, try it. __Try it even if you don't use Sublime Text__. You'll have to switch between two text editors, but you already have to switch between your editor and your HTTP client. Sublime Text running Requester probably has a smaller footprint than your HTTP client, and it's probably a lot easier to use. ✨✨
