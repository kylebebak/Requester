## Requester Tutorial
~~~py
requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

get('https://jsonplaceholder.typicode.com/posts')  # 'requests.' prefix is optional
post('jsonplaceholder.typicode.com/posts')  # as is the URL scheme
~~~

Place your cursor on one of the lines in the code block above and hit <kbd>ctrl+alt+r</kbd> (<kbd>ctrl+r</kbd> on macOS). Or, look for __Requester: Run Requests__ in the command palette and hit Enter. A response tab will appear, with a name like __GET: /albums__.

>If this doesn't work, __and you're seeing errors__ every time you run a request, this probably means the __requests__ dependency wasn't installed successfully. To fix this, look for __Package Control: Satisfy Dependencies__ in the command palette, run it, and restart Sublime Text.

Head to the response tab and check out the response. Hit <kbd>ctrl+alt+r</kbd> or <kbd>ctrl+r</kbd> (<kbd>ctrl+r</kbd> or <kbd>cmd+r</kbd> on macOS) to replay the request. You can edit the request, which is at the top of the file, before replaying it.

Now, go back to the requester file and highlight all 5 lines, and once again execute the requests.

Tabs will open for all 4 requests (Requester conveniently ignores the blank line). Before checking out these tabs, execute the requests yet again. You'll notice duplicate requests don't create a mess of new tabs, but simply overwrite the content in the matching response tabs.

Want to see something nifty? Mix up the order of the 4 open response tabs, come back to the tutorial tab, and run __Requester: Reorder Response Tabs__.


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


### Pinned Response Tabs
When you execute a request, Requester overwrites response tabs that have the same request method and URL as the request you're executing. Hmmm... Does this mean you can't open multiple response tabs for the same request?

Of course not! In the response tab, go the command palette and look for __Requester: Pin/Unpin Response Tab__, or look in the response tab for the keyboard shortcut to __pin/unpin tab__. Try it: pin a response tab, go to the requester file, and execute the same request again.


### Environment Variables
It's time to refactor your requests to use environment variables. Requester has a fully featured scripting language for env vars... Python!

You can define them directly in your requester file. Just put your variables in a code block fenced by __###env__ lines.

~~~py
###env
base_url = 'https://jsonplaceholder.typicode.com'
###env

get(base_url + '/albums')
post(base_url + '/albums')
~~~

Try executing these requests. Nice, huh?

The __###env__ lines must have no leading or trailing spaces. Only the first env block in a requester file will be used.


### Request Body, Query Params, Custom Headers, Cookies
~~~py
post('httpbin.org/post', data={'key1': 'value1', 'key2': 'value2'})

post('httpbin.org/post', json=[1, 2, 3])
post('httpbin.org/post', json={'name': 'Jimbo', 'age': 35, 'married': False, 'hobbies': ['wiki', 'pedia']})

get('httpbin.org/get', params={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/headers', headers={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/cookies', cookies={'key1': 'value1', 'key2': 'value2'})

get('httpbin.org/redirect-to?url=foo')
# response tab shows redirects
~~~

Body, Query Params, Headers and Cookies can be passed to __requests__ as dictionaries.

If you execute the last request, you'll notice the response tab shows the series of redirects followed by the browser. If you want to disallow redirects by default, simply change Requester's `allow_redirects` setting to `false`.

__Requester's syntax is Requests syntax__. If you don't know how to do something, just have a look at the [Requests Quickstart](http://docs.python-requests.org/en/master/user/quickstart/).


### New Requester File
Want to start a new collection of requests? Run __Requester: New Requester File__ from the command palette. You'll get a new file pointing to an empty env file, with an empty env block, and with a link to Requester's syntax at the top.


## More Info
This tutorial is not meant to be complete, and if you have doubts about how Requester works the README has the goods. Check it out [here](https://github.com/kylebebak/Requester) or by running __Requester: Show Documentation__!
