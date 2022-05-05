## Installation

1. Download and install [Sublime Text 3](https://www.sublimetext.com/3).
2. Install [Package Control for Sublime Text](https://packagecontrol.io/).
3. Open the command palette <kbd>shift+cmd+p</kbd> and type **Package Control: Install Package**.
4. Search for **Requester** (not ~~Http Requester~~) and install it.

## Getting Started

Open the interactive tutorial in Sublime Text! Look for **Requester: Show Tutorial** in the command palette. Alternatively, just keep reading.

Open a file and insert the following.

```py
requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

post('https://jsonplaceholder.typicode.com/posts')  # 'requests.' prefix is optional
get('jsonplaceholder.typicode.com/posts')  # as is the URL scheme
```

Place your cursor on one of the lines and hit <kbd>ctrl+alt+r</kbd> (<kbd>ctrl+r</kbd> on macOS). Or, look for **Requester: Run Requests** in the command palette <kbd>shift+cmd+p</kbd> and hit Enter. A response tab will appear, with a name like **GET: /albums**.

Head to the response tab and check out the response. Hit <kbd>ctrl+alt+r</kbd> or <kbd>ctrl+r</kbd> (<kbd>ctrl+r</kbd> or <kbd>cmd+r</kbd> on macOS) to replay the request. You can edit the request, which is at the top of the file, before replaying it.

Now, go back to the requester file and highlight all 5 lines, and once again execute the requests.

Tabs will open for all 4 requests (Requester conveniently ignores the blank line). Before checking out these tabs, execute the requests yet again. You'll notice duplicate requests don't create a mess of new tabs, they just overwrite the content in the matching response tabs (read on if you'd like to change this behavior).

### Jump to Request

Go back to your requester file and save it as `<anything>.pyr`. The extension is important. Run Sublime Text's **Goto Symbol** by pressing <kbd>ctrl+r</kbd> (<kbd>cmd+r</kbd> on macOS). If your requester file has this extension, you can jump between your requests almost instantaneously.

### Multiline Requests

For executing requests defined over multiple lines, you have three options:

- fully highlight one or more requests and execute them
- place your cursor on the first line of a request and execute it
- place your cursor **anywhere inside** a request and execute it (super convenient, and works as long as the view's syntax recognizes Python function calls)

```py
get(
    'https://jsonplaceholder.typicode.com/posts'
)
post(
    'jsonplaceholder.typicode.com/posts'
)
```

Notice that if a URL scheme isn't supplied, Requester sets it as `http` by default.

If you want to close all open tabs, look for **Requester: Close All Response Tabs** in the command palette.

### JSON Response Formatting

Requester supports 3 options for JSON response formatting, `indent_sort`, `indent`, and `raw`. The default value for all requests, which can be changed in Requester's settings, is `indent_sort`. If you don't want keys in objects sorted alphabetically, use `indent` or `raw`.

```py
get('http://headers.jsontest.com/', fmt='indent_sort')
get('http://headers.jsontest.com/', fmt='indent')
get('http://headers.jsontest.com/', fmt='raw')
```

### Ergonomic GET Requests

Try sending the following requests. This is obviously not valid Python syntax, but Requester has a shortuct for basic GET requests. If you run Requester on a URL like the one below, it automatically wraps it like so: `requests.get('<url>')`. And it doesn't wrap the URL in quotes if it's already got them.

```py
httpbin.org/get
'httpbin.org/headers'
```

### Pinned Response Tabs

When you execute a request, Requester overwrites response tabs that have the same request method and URL as the request you're executing. If you want multiple views into the same request, you can **pin** your response tabs. Pinned response tabs are never overwritten.

In a response tab, go to the command palette and look for **Requester: Pin/Unpin Response Tab**, or look in the response tab for the keyboard shortcut to **pin/unpin tab**.

### Custom Tab Name

Use the `tabname` argument to specify a custom response tab name for your request. The response in this tab can only be overwritten by a request with the same value for the `tabname` argument.

Check out the requests below. Execute the first one, wait for the response tab to open, then execute the second one.

```py
post('httpbin.org/post', json={'a': 'b'}, tabname='ab')
post('httpbin.org/post', json={'c': 'd'}, tabname='cd')
```

This is useful for differentiating requests whose method and URL are the same but whose meaning is different. GraphQL requests, whose meaning is encoded in the query string, are one example.

The `tabname` is also included in the fuzzy searchable request history. After executing one of the above requests, try searching your request history for "cd -".

### Save Request Back To Requester File

Imagine you're debugging a request in a response tab, replaying and modifying the request as you go. Requester lets you save this modified request back to the requester file from which you sent it.

In a response tab, go to the command palette and look for **Requester: Save Request Back To Requester File**, or look in the response tab for the keyboard shortcut to **save request**.

If the requester file exists and you haven't changed your original request since you sent it, Requester opens the requester file, scrolls to the original request, and overwrites it with the modified one from your response tab. You can repeatedly save back a request as you edit it in the response tab. ✨✨

### Environment Variables

Requester has a powerful scripting language for env vars... Python!

You can define them directly in your requester file. Just put your variables in a code block fenced by **###env** lines. Try executing these requests.

```py
###env
base_url = 'https://jsonplaceholder.typicode.com'
###env

get(base_url + '/albums')
post(base_url + '/albums')
```

Variables you define in your env block can be referenced by any of your requests. The **###env** lines must have no leading or trailing spaces. Only the first env block in a requester file is used.

You can import and use anything in Python's standard library in your env block. You can also import and use `requests`. This makes Requester's env vars **powerful and flexible**. Here's a toy example. Copy it to another file and give it a try.

```py
###env
import requests
base_url = 'https://www.metaweather.com/api'
r = requests.get(base_url + '/location/search/?lattlong=19.4326,-99.1332')
woeid = str(r.json()[0]['woeid'])  # get "where on earth id" for Mexico City
###env

get('{}/location/{}/'.format(base_url, woeid))  # use "where on earth id" to get Mexico City's weather data
```

## Advanced Features

Find out what makes Requester really special. In the future if you need to refresh your memory, just press <kbd>shift+cmd+p</kbd> to open the command palette, and type **Requester**.

### Request Body, Query Params, Custom Headers, Cookies

```py
post('httpbin.org/post', data={'key1': 'value1', 'key2': 'value2'})

post('httpbin.org/post', json=[1, 2, 3])
post('httpbin.org/post', json={'name': 'Jimbo', 'age': 35, 'married': False, 'hobbies': ['wiki', 'pedia']})

get('httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/redirect-to?url=foo')  # response tab shows redirects
```

Body, Query Params, and Headers are passed to **requests** as dictionaries. Cookies can be passed as a dict or an instance of `requests.cookies.RequestsCookieJar`.

If you execute the last request, you'll notice the response tab shows the series of redirects followed by the browser.

> If you want to disallow redirects by default, simply change Requester's `allow_redirects` setting to `false`.

### Sessions

Need to log in first so all your requests include a session cookie? [Session objects](http://docs.python-requests.org/en/master/user/advanced/#session-objects) make this a cinch.

Instantiate the session object in the env block and use it in your requests. Copy this code to a new file, run the request, and check out the `session_id` cookie in the request headers.

```py
###env
import requests
s = requests.Session()
s.get('http://httpbin.org/cookies/set?session_id=12345', timeout=5)
###env

s.get('http://httpbin.org/get')
s.get('http://httpbin.org/cookies/set?token=789')
```

In the example above, each time you execute **Requester: Run Requests**, a new session is created, and once all responses are returned the session is destroyed.

If you highlight and run multiple requests that depend a session `s`, they will all share the same session `s`. If you run them serially, you can control the order in which cookies are added to the session.

If you need to send [prepared requests](http://docs.python-requests.org/en/master/user/advanced/#prepared-requests) for some reason, e.g. to use a self-signed SSL certificate, just prepare your request and session in the env block, and use `s.send` to send the request.

### Authentication

Requests has [excellent support for authentication](http://docs.python-requests.org/en/master/user/authentication/). **Basic Authentication** and **Digest Authentication** are built in, and adding custom auth schemes is easy.

To use a custom auth scheme with Requester you define the auth class in your env block or env file, then pass an instance of this class to the `auth` argument of a request.

Requester comes with a few pre-written auth schemes, you can use in your code, or as a reference. Run **Requester: Authentication Options** in the command palette to see the list. Have a look at **Token** auth, which simplifies passing a token in the **"Authorization"** header of your requests.

#### OAuth1 and OAuth2

**requests-oauthlib** is bundled with Requester, which provides first-class support for [OAuth1](https://github.com/requests/requests-oauthlib) and [OAuth2](https://requests-oauthlib.readthedocs.io/en/latest/oauth2_workflow.html).

Let's say you want explore the Twitter REST API, which uses OAuth1 for authentication. Go to <https://apps.twitter.com/app/new>, create a new application, then go to the **Keys and Access Tokens** tab for your application. Generate an access token and an access token secret, grab your API key and secret, and pass them to `OAuth1`.

```py
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
```

### Forms and File Uploads

Requests makes posting forms and uploading files easy. See how in the Requests documentation.

- [Forms](http://docs.python-requests.org/en/latest/user/quickstart/#more-complicated-post-requests)
- [File uploads](http://docs.python-requests.org/en/latest/user/quickstart/#post-a-multipart-encoded-file)
- [Multiple file uploads](http://docs.python-requests.org/en/master/user/advanced/#post-multiple-multipart-encoded-files)

Requests also supports streaming and chunked file uploads, which is great (and necessary) if the file you're uploading doesn't fit in memory, but the API is a bit more complicated. Requester has the special `streamed` and `chunked` arguments to make these uploads trivial.

```py
post('https://requestb.in/<your_request_bin>', streamed='/path/to/file')
post('https://requestb.in/<your_request_bin>', chunked='/path/to/file')
```

If you pass the file as a `chunked` upload, the **"Transfer-Encoding": "chunked"** header is added to your request. Some servers don't allow chunked uploads, in which case you can use a `streamed` upload. If they're an option, chunked uploads are nicer: they come with a progress bar and can be cancelled.

> If you need streaming uploads for multipart forms, or uploads of multiple files, the `requests-toolbelt` package has your back. Check out [this section](#import-any-python-package-in-requester-env).

### Downloads

Requester also provides Wget-style downloads. Just add the `filename` keyword arg to a call to `requests.get`.

```py
get('http://www.nationalgeographic.com/content/dam/animals/thumbs/rights-exempt/mammals/d/domestic-dog_thumb.jpg', filename='image.jpg')
```

As with streamed and chunked uploads, `filename` can be an absolute path, or a path relative to your requester file. Also, as with uploads, **multiple downloads can be executed in parallel**. Downloads can be cancelled. They come with a nice progress bar.

#### Downloaded File Name

If you pass the path of an existing directory for `filename`, Requester will download the file to this directory and infer the name of the file from the URL.

In this mode, if the file name already exists, Requester adds a suffix to make the file name unique. Try downloading this file several times in succession.

```py
get('http://www.nationalgeographic.com/content/dam/animals/thumbs/rights-exempt/mammals/d/domestic-dog_thumb.jpg', filename='~/Desktop')
```

### Cancel Outstanding Requests

If you have outstanding requests that are taking a while to return, and you don't want to wait for them to time out, you can cancel them by calling **Requester: Cancel Requests** from the command palette.

### Chaining Requests

If you need to run requests or tests one after another, in the order in which they're defined in your requester file, look for **Requester: Run Requests Serially** or **Requester: Run Tests Serially** in the command palette.

Behind the scenes, this just passes the `concurrency=1` arg to `requester` or `requester_run_tests`, and voilà, you've chained your requests.

> Note: code inside your **env block/env file** always runs serially, which includes any requests you put in there.

#### Chaining by Reference

If you need **true** request chaining, such that a request can reference the `Response` object returned by the previous request, that's easy too. Requester lets you reference the most recently returned response using the `Response` variable, and also lets you **name** your responses. Copy the following code to a new view, highlight it, and run **Requester: Run Requests Serially**.

```py
get('http://httpbin.org/get')

get('http://httpbin.org/cookies', cookies={'url': Response.json()['url']})
```

If you don't run requests serially, the second request fails, because it's executed before the first request returns. Now try **naming** the response from a request using the `name` argument.

```py
get('httpbin.org/get', name='first_response')
get('google.com', allow_redirects=False)
get('httpbin.org/cookies', cookies={'url': first_response.json()['url']})
```

> By the way, you shouldn't name an env var "Response", or with the same name that you pass to a request's `name` argument, because it will be overwritten.

## Navigation and History

UX is central to Requester's design. The biggest UX difference between Requester and other HTTP clients is the ease with which you can find, modify and execute your requests — the ones in your requester file, and the ones in your request history.

### Requester File Navigation (.pyr extension)

Try running **Requester: New Requester File** from the command palette. You'll get a file pointing to an empty env file, with an empty env block, and a link to Requester's syntax at the top. It's ready for starting a new collection of requests.

You'll notice the file you just created has a special extension, `.pyr`. This is the Python Requester extension. **You should save all your requester files with this extension**.

Here's why. Run **Requester: New Requester File (Navigation Demo)** from the command palette. You'll get a new requester file with some stub requests already inserted. Now, run Sublime's **Goto Symbol** command (<kbd>cmd+r</kbd> on macOS)... You can jump between request groups and individual requests almost instantaneously using fuzzy search!

Behind the scenes, `.pyr` files get the special **Requester** syntax applied to them (you can set this syntax on any view you like by running **Set Syntax: Requester** from the command palette). **Requester** is the default Python syntax with a few Requester-specific improvements:

- your `###env` block delimeters are highlighted
- request groups can be declared by starting a line with two or more `##` characters
- you can use Sublime's **Goto Symbol** to jump between requests and request groups ✨✨

### Request History

Requester saves a history of executed requests. Call **Requester: Request History** to check it out. They appear in reverse chronological order and include each request's age, URL, response status code, and requester file. They're fuzzy searchable!

Choose an old request and select it. A special response tab will open, with the request string, some response metadata, and the usual response tab commands, but nothing else.

Replay the chosen request. It runs as if it were executed from its original requester file, but it also pulls in up-to-date env vars from the env block and the env file.

> Requests are keyed for uniqueness on `(request_string, requester_file)`, which allows you to persist identical request strings from different requester files.

> If you use the `tabname` argument with your request, this argument is also fuzzy searchable. See [this section](#custom-tab-name) for more details.

#### Page Through Past Requests

Notice the key bindings for **prev/next request** in response tabs? Give them a try.

> If these or other bindings don't work, don't fret! Here's a 1 minute, [permanent fix to the problem](#response-tab-commands).

These commands let you page through past requests one at a time, and can be used from any response tab. **Combine them with fuzzy search for request searching nirvana**.

Imagine you want to find a GET request you ran when you were working with the Twitter API over the weekend. You open search with **Requester: Request History** and type _twitter_, and see a bunch of requests from around 3 days ago. You're not sure which is the right one, so you hit Enter to get a better look.

From here, you begin to page back, past a few 40Xs, some POSTs, then boom, the elusive 200 GET is right in front of you. You replay it, and now it's back on top of your request history. Next time you want it it'll take 1 second to find instead of 10.

---

Requester's history is one of Requester's most convenient features, which means you might want to modify your keymap and bind something to **requester_history**. ✨✨

Open your keymap from the command palette by running **Preferences: Key Bindings**. For example, on macOS you might bind it to <kbd>ctrl+h</kbd> by adding the following:

```json
{ "keys": ["ctrl+h"], "command": "requester_history" },
```

#### Delete Requests From History

Iterating on a request to get it right can take time. You might inadvertently fill your request history with requests you'd rather forget.

You can delete a request from your history by pressing <kbd>ctrl+alt+backspace</kbd> in the history tab. To undo your delete, just replay the request before closing the history tab.

#### Moving Your Requester File

Is not as simple as dragging it from one folder to another... Why not? Because when you send a request from a requester file, the requester file's path is saved along with other metadata in your request history.

If you move your requester file, the history entries for requests sent from this file now point to a file that no longer exists! You'd have to update these entries to point to the new path of your requester file.

Editing your history file by hand is not advised: if you mess something up, the file might become corrupted. Fortunately, Requester comes with a command that moves your requester file to a new path, and updates all the relevant history entries for you. Just go to your requester file, look for **Requester: Move Requester File** in the command palette, and choose a new path for your requester file.

### Explore Hyperlinked APIs (HATEOAS)

Ever used an API that returns **hyperlinks** to other resources in the response? This pattern is part of a larger concept in REST called HATEOAS, or [hypermedia as the engine of application state](http://www.django-rest-framework.org/topics/rest-hypermedia-hateoas/).

It's a mouthful, but the idea is simple: an API response should tell clients how to interact with related resources by providing them hyperlinks to those resources. This allows APIs to change without breaking clients, as long as clients are written to take their cues from the hyperlinks returned by the API.

**Requester is ready-made for exploring these APIs**. From a response tab, highlight any URL and press <kbd>ctrl+e</kbd> (<kbd>cmd+e</kbd> on macOS). Instead of replaying the original request, Requester sends a GET request to the highlighted URL and opens the response in a new tab.

It also compares the domain of the highlighted URL with the domain of the original request. If they're the same, Requester **includes the same args and kwargs in the new request**. If the original request was authenticated, the "exploratory" request will be authenticated as well.

If the domains are not the same, Requester strips all additional args and kwargs from the request, to ensure that none of your auth credentials are sent to a URL not belonging to the "source" API.

```py
post('httpbin.org/post',
    headers={'Authorization': 'Bearer my_secret_token'},
    json={'same_domain': 'http://httpbin.org/get', 'other_domain': 'https://jsonplaceholder.typicode.com/posts'}
)
```

Execute the request above. In the response tab, try highlighting each of the URLs in the response body and sending exploratory requests. Requester makes it trivial to explore hyperlinked URLs without worrying about leaking your credentials. ✨✨

### Options Requests

Want to see which HTTP verbs a given endpoint accepts? Send an `OPTIONS` request to the endpoint. Requester makes this ridiculously easy -- from a response tab, just press <kbd>ctrl+o</kbd> (<kbd>cmd+o</kbd> on macOS).

## More on Env Vars

Env vars are one of Requester's most powerful features. This section explains everything you can do with them, and how they work in detail.

### Separate Env File

Requester can save and source your env vars from a separate env file. To do this, first you want to save your requester file. This way you can use a **relative path** from your requester file to your env file, which is convenient. Save it with any name (using the `.pyr` extension of course). `requester.pyr` is fine.

Next, save a file with the name `requester_env.py` in the same directory as `requester.pyr`, and add an env var to it.

```py
base_url = 'https://jsonplaceholder.typicode.com'
```

Finally, define the path of your `env_file` in your requester file like so:

```py
env_file = 'requester_env.py'

get(base_url + '/albums')
post(base_url + '/albums')
```

Requester will now look for the env file at the path `requester_env.py`, which is relative to the location of the requester file. You can change this path to any relative path you want, e.g. `relative/path/to/env.py`. You can also use an **absolute path** to the env vars file if you want.

#### Merging Vars from Env Block and Env File

Is totally fine!

Why? If you're working on a team, you might want you requester file in version control. Static env vars can be defined in the env block of your requester file.

Dynamic env vars, like a `base_url` that could point to staging one minute and production the next, can be defined in an env file. Put the env file in your `.gitignore`. This way devs can tweak their envs without making useless commits or stepping on each other's toes.

What if a var has the same name in the env block and the env file: which one takes precedence? This depends on where you put your **env block** and the `env_file` line in your requester file. Check out the examples below:

```py
env_file = 'vars.py'

###env
base_url = 'https://jsonplaceholder.typicode.com'
###env

get(base_url + '/albums')
```

vs...

```py
###env
base_url = 'https://jsonplaceholder.typicode.com'
###env

env_file = 'vars.py'

get(base_url + '/albums')
```

In the first example, because `env_file` is declared **before** the env block, the vars in the env block override any identically named vars in the env file.

In the second example, because `env_file` is declared **after** the env block, the reverse is true. The vars in the env file override any identically named vars in the env block.

### How Env Vars are Parsed

If env vars aren't behaving the way you expected, or you just want to know how Requester computes an env before requests are run, read on.

Requester computes an env by evaluating an env string, which is the concatenation of an env block and the contents of an env file.

If the request is sent from a normal view, Requester tries to get the env string from the contents of the view (which is exactly what you'd expect).

---

If the request is resent from a response tab, Requester tries to get the env string from the requester file from which the request was originally sent.

If that file has been deleted, or the request wasn't originally sent from a saved file, Requester uses the same env string as the one that was computed originally.

This means if you resend a request and you've since changed the env vars in the requester file, the request uses the updated env vars. If you've since deleted the requester file, the request uses the same env vars it used when it was first sent. If you haven't deleted the requester file, but you deleted an env var used by the request, the request fails.

That Requester retrieves updated env vars from the requester file when resending a request might seem like a matter of taste, **but on balance it's very convenient**. If you hit a protected API that requires an auth token or cookie, just put the credentials in your env vars. When your credentials expire, go to your env vars and update them. The old requests you sent, whose original credentials are no longer valid, **will just keep working**.

### Import Any Python Package In Requester Env

Requester comes bundled with a few packages (`requests`, `requests-oauthlib`, `requests-toolbelt`, `jsonschema`) that you can import in an env block or env file, but you can trivially extend it to import **any** Python 3 package in its env. All you have to do is set Requester's `packages_path` setting to a directory with Python 3 packages. Requester can then import these packages in your env block or env file. ✨✨

In my settings for Requester `packages_path` points to a Python 3 virtual env: `/Users/kylebebak/.virtualenvs/general/lib/python3.5/site-packages`. I use `pip` to install these packages.

#### Pip3 Quickstart

If you don't have `virtualenv` or you're not comfortable using it, the quick solution is to install Python 3, which will install `pip3` and `python3` executables. Run `which pip3` to make sure you've done this.

Then run `pip3 install <package>`, and so on for whatever packages you'd like to use with Requester.

Finally, run `pip3 show <package>`, and look for the **LOCATION** field in the output. Now you know where pip is installing your packages.

Use this path as your `packages_path` setting in Requester's settings file. To open these settings, look for **Requester: Settings** in the command palette.

> Note: Sublime Text runs Python 3.3, and there are some packages, such as `browsercookie`, that can only be imported by Sublime Text if they are downloaded with `pip3.3`. The best way to download Python 3.3 is with [pyenv](https://gist.github.com/Bouke/11261620), but this can be a pain. My advice: don't bother unless you really want to use one of these packages.

#### Cookies Interceptor

Want to use sessions currently open in your browser in requests sent by Requester? Look for **Requester: Authentication Options** and choose **Cookies Interceptor**.

This depends on the [browsercookie](https://bitbucket.org/richardpenman/browsercookie) package, which must be installed with the same version of Python 3 as the one used by Sublime Text. See the **Note** in the [pip3 quickstart section](#pip3-quickstart).

## GraphQL

Requester provides full support for GraphQL. It provides a shorthand for the `query`, `variables`, and `operationName` params described in the [GraphQL spec](http://graphql.org/learn/serving-over-http/), for both **GET** and **POST** requests, via the `gql`, `gqlv`, `gqlo` kwargs.

`gqlv` and `gqlo` have no effect unless `gql` is also passed. For GET requests, the params are URL encoded and added to the query string. For POST requests, they get JSON encoded and added to the request body, as described in the spec.

Here's an example, hitting [this countries GraphQL API](https://countries.trevorblades.com/).

```py
requests.post('https://countries.trevorblades.com/', gql="""
{
  continents {
    name
    code
  }
  country(code: "BZ") {
    name
    currency
    languages {
      name
      code
    }
  }
}
""")
```

### Browsing GraphQL APIs: Autocomplete and Linting

Requester provides autocomplete/autosuggest and linting for GraphQL queries, like [GraphiQL](https://github.com/graphql/graphiql), which makes browsing GraphQL APIs a breeze. Simply run a request with the `gql` arg. Then, from the response tab, **start typing the name of a field in your gql string**, or from an **empty line in your gql string**, press <kbd>ctrl+space</kbd> to get a list of valid fields that can be inserted at your cursor's position.

Requester lints your query and displays syntax errors with their line and column numbers. More detailed debug information is printed to the Sublime Text console. Try it on one of the requests above.

> If autocomplete doesn't work, it's probably being overridden by another autocomplete package, like **All Autocomplete**, **tern_for_sublime**, etc. Remove these packages, or disable them for Requester response views if possible.

> GraphQL autocomplete will never override autocompletions provided by your other packages.

## Test Runner

Requester has a built-in test runner! Copy and paste this into an empty file.

```py
###env
base_url = 'https://jsonplaceholder.typicode.com'
prop = 'status_code'


def email_is_correct(res):
    import re
    return re.match(r'[^@]+@[^@]+\.[^@]+', res.json()[0]['email']) is not None
###env

# first request
get(base_url + '/posts')
assert {prop: 200, 'encoding': 'utf-8'}

# second request, with no assertion
get(base_url + '/profile')

# third request
get(base_url + '/comments')
assert {'status_code': 500}

# fourth request, using a user-defined validation function
get(base_url + '/comments')
assert {'function': email_is_correct}
```

Highlight all the requests, look for **Requester: Run Tests** in the command palette, and run it. You'll notice that test results are displayed for the first, third and fourth requests.

What's going on here? If a request has an assertion below it, the `key, value` pair in the assertion is compared with the returned `Response` object. For the first and third requests, if `key` is a valid property of the `Response` object, `value` is compared with the property. If they're not equal discrepancies are displayed.

Some valid properties: `apparent_encoding`, `cookies`, `encoding`, `headers`, `history`, `is_permanent_redirect`, `is_redirect`, `json`, `links`, `reason`, `status_code`, `text`, `content`.

### Custom Validation Functions

Notice the assertion in the fourth request, `assert {'function': email_is_correct}`? If your assertion key starts with "function", then the corresponding value must be a function that is defined in your env block or your env file.

The function receives [the response object](http://docs.python-requests.org/en/master/api/#requests.Response) as its only argument, and must return `True` or `False`. If it returns `False`, the test fails, else it passes.

Take a closer look at the definition of `email_is_correct`... **Custom validation functions** allow you to make assertions about any aspect of your response object, using anything that Python has to offer!

### Making Assertions About Response Structure

`cookies`, `headers` and `json` point to Python dicts or lists, which means comparing for equality isn't very useful. Much more useful are the following special assertion keys for these properties: `cookies_schema`, `headers_schema`, `json_schema`.

Including one of these in an assertion will validate the corresponding property with [jsonschema.validate](https://github.com/Julian/jsonschema). **This lets you describe the structure of cookies, headers, and JSON responses returned by your API**. Look at the example below. The test fails because we assert that the `userId` for each object in the array of results has a type of `string`, and this isn't true.

If you have a JSON API, [JSON Schema](http://json-schema.org/) is an excellent way to describe your API's data format.

```py
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
```

The test runner was built for convenience:

- requests and assertions can use env vars
- requests without corresponding assertions are ignored
- the order of requests is preserved in the results tab

Assertions can be inserted seamlessly into a requester file; if you're not doing a test run they're simply ignored.

### Export Tests to Runnable Script

If you want to integrate your Requester tests into your app's test routine, Requester can export request/assertion pairs to a runnable test script. Highlight the requests and assertions you want to export and look for **Requester: Export Tests To Runnable Script** in the command palette.

This test script depends only on the Python `requests` and `jsonschema` packages. To run it from the command line you just call `python -m unittest <test_module_name>`. The default test module name is **requester_tests**.

The test export command lacks two conveniences available to all other Requester commands:

- it doesn't automatically include the timeout argument in calls to `requests`
- it doesn't automatically add a scheme to URLs with no scheme

## Benchmarking Tool

Want to see how your staging or production servers hold up under load? Requester's benchmarking tool is like [ab](https://httpd.apache.org/docs/2.4/programs/ab.html) or [siege](https://www.joedog.org/siege-home/), but it's easier to use. Highlight one or more requests, and call **Requester: Run Benchmarks** from the command palette.

You'll be prompted for the number `N` of each request to run, and the concurrency `C`. In other words, if you highlight 5 requests, then input 100 for `N` and 20 for `C`, you'll send a total of 500 requests, 100 to each endpoint, in bunches of 20 at a time.

Requester then displays a profile with response time metrics, grouped by request method and URL. Try it on these 3 here, with N=100 and C=20.

```py
get('http://httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('http://httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})
```

It goes without saying, but please don't use this for DoS attacks on servers you don't own. Regardless of what you pass for `N`, the total number of requests executed is capped at 100000. `C` is capped at 1000, which translates to [tens of millions of requests per day](https://serverfault.com/questions/274253/apache-ab-choosing-number-of-concurrent-connections).

> Warning: benchmarks runs with `C` above ~100 may slow down the UI while they are running.

## Export/Import with cURL, HTTPie

Need your requests in a more portable format? Requester can export to and import from the ubiquitous [cURL](https://curl.haxx.se/) format.

This makes it trivial to share requests with teammates who don't use Requester, or execute your requests on any server you like.

Prefer [HTTPie](https://httpie.org/) instead of cURL? You can also export requests to HTTPie!

Exporting works seamlessly with env vars. Just highlight a group of requests and look for **Requester: Export To cURL** or **Requester: Export To HTTPie** in the command palette. For importing it's **Requester: Import From cURL**. Exporting to HTTPie supports a bunch of features, including basic and digest authentication, file downloads, and even sessions. For sessions, just highlight your env block along with the requests you want to export.

### Debugging/Exploring Network Activity

cURL is the lingua franca of HTTP clients. Want to explore requests made by some site you're trying to scrape or reverse-engineer?

Open your browser's developer tools, go to the network tab, filter on `XHR` if you want, and refresh the page. Find the request you're looking for and copy it as cURL. Bring it into Sublime, run **Requester: Import From cURL**, and run your request.

In less than a minute you can pull requests, credentials and all, out of your browser and into your laboratory.

## Special Keyword Arguments

Requester's syntax is basically identical to Requests' syntax, but it adds support for the following special `kwargs`.

- **fmt**: one of ('raw', 'indent', 'indent_sort'), controls formatting of JSON responses
- **name**: binds name to response object so that it can be referenced by subsequent serially executed requests
- **tabname**: specifies name of response tab, and ensures tab can only be overwritten by requests with the same **tabname**; is included in fuzzy searchable request history
- **filename**: downloads the response to the specified path
- **streamed**: performs a streaming upload of the specified file
- **chunked**: performs a chunked upload, with a progress indicator, of the specified file
- **gql**, **gqlv**, **gqlo**: adds the specified string to `query`, `variables` and `operationName` params, for GET and POST requests to GraphQL endpoints

## Commands

Commands defined by this package, in case you want to add or change key bindings.

- **requester**
- **requester_replay_request**
- **requester_explore_url**: explore url in response tab
- **requester_save_request**: save request back to requester file
- **requester_history**: search and re-execute past requests
- **requester_delete_request_history**: delete request from history (history tab only)
- **requester_open_request_history_file**: open request history file in read only view
- **requester_move_requester_file**: move requester file to new path and update request history for all requests sent from this file
- **requester_cancel_requests**: cancel all outstanding requests
- **requester_cancel_downloads**: cancel outstanding file downloads
- **requester_cancel_uploads**: cancel outstanding file uploads
- **requester_response_tab_toggle_pinned**: pin (or unpin) a response tab so that it isn't overwritten by requests with its same method and URL
- **requester_close_response_tabs**
- **requester_reorder_response_tabs**: reorders response tabs to match order of requests in requester file
- **requester_new_requester_file**: create empty requester file
- **requester_run_tests**
- **requester_export_tests**: export tests to runnable script
- **requester_prompt_benchmarks**
- **requester_auth_options**
- **requester_export_to_curl**: export selected requests to cURL
- **requester_export_to_httpie**: export selected requests to HTTPie
- **requester_import_from_curl**: import selected cURL requests
- **requester_show_tutorial**
- **requester_show_documentation**
- **requester_show_syntax**

## Response Tab Commands

The following commands are only available in response tabs. The key bindings listed below are for macOS. Response tabs show (most of) these key bindings.

- **cmd+r**: replay request
- **ctrl+alt+ ←/→**: prev/next request
- **ctrl+alt+ backspace**: delete request from history (only works in history tab)
- **cmd+t**: pin/unpin tab
- **cmd+e**: explore URL
- **cmd+o**: options
- **ctrl+space**: GraphQL autocomplete
- **cmd+s**: save request back to requester file

If you try to execute one of these commands and nothing happens, you've already mapped the binding to another command. Run **Preferences: Key Bindings** from the command palette, find the conflicting key combination, add the following `context` to the binding, and restart Sublime Text.

```json
"context": [
  { "key": "setting.requester.response_view", "operator": "equal", "operand": false }
]
```

This removes the conflict by disabling your binding **only** in Requester's response views.

## Settings

Requester's modifiable settings, and their default values. You can override any of these settings by creating a `Requester.sublime-settings` file in Sublime's `Packages/User` directory. The easiest way to do this is go to **Preferences > Package Settings > Requester > Settings** from the menu bar, or look for **Requester: Settings** in the command palette.

- **timeout**, `15`: default timeout in seconds for all requests
- **timeout_env**, `15`: default timeout in seconds for executing env block/env file
- **allow_redirects**, `true`: are redirects allowed by default?
- **scheme**, `"http"`: scheme prepended to URLs in case no scheme is specified
- **fmt**, `"indent_sort"`: JSON response formatting, one of ("raw", "indent", "indent_sort")
- **max_content_length_kb**, `5000`: don't render responses whose content length (kilobytes) exceeds this value
- **change_focus_after_request**, `true`: if a single request is executed, change focus to response tab after request returns
- **reorder_tabs_after_requests**, `false`: if multiple requests are executed, automatically reorder response tabs based on requests in requester file after requests return
- **pin_tabs_by_default**, `false`: pin newly opened response tabs by default, so they aren't overwritten by requests with the same method and URL
- **response_tab_name_length**, `32`: max length of name of response tabs
- **history_file**, `"Requester.history.json"`: name of request history file, stored in User directory
- **history_max_entries**, `250`: max number of requests in history file
- **chunk_size**, `1024`: chunk size for file downloads (bytes)
- **only_download_for_200**, `true`: only perform file download if response status code is 200
- **packages_path**, `""`: absolute path to extra python packages included in env

## Contributing and Tests

[See here](https://github.com/kylebebak/Requester/blob/master/CONTRIBUTING.md).

## Inspired By

- [Requests](http://docs.python-requests.org/en/master/) — Requester sends all its requests using this amazing library.
- [HTTPie](https://github.com/jakubroztocil/httpie) — A truly Pythonic tool. Its focus on intuitiveness and ergonomics inspired many of Requester's features, including its [docs site](https://kylebebak.github.io/Requester/).
- [Postman](https://www.getpostman.com/) — A strong influence on much of Requester's "managed" UI.

## Release Notes

[See Requester's version history here](https://github.com/kylebebak/Requester/blob/master/messages/release_notes.txt).

## Requests

The last version of Requests that supports Python 3.3 is **2.18.3**. This is the version bundled with Requester. Hopefully the next iteration of Sublime Text will support a more recent Python version!

Here's Requests' [version history](http://docs.python-requests.org/en/master/community/updates/).
