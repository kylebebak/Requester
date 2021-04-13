## Installation
1. Download and install [Sublime Text 3](https://www.sublimetext.com/3).
2. Install [Package Control for Sublime Text](https://packagecontrol.io/).
3. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
4. Search for __Requester__ (not ~~Http Requester~~) and install it.


## Getting Started
Open the interactive tutorial in Sublime Text! Look for __Requester: Show Tutorial__ in the command palette.

Or, open a file and insert the following.

~~~py
requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

get('https://jsonplaceholder.typicode.com/posts')  # 'requests.' prefix is optional
post('jsonplaceholder.typicode.com/posts')  # as is the URL scheme
~~~

Place your cursor on one of the lines and hit <kbd>ctrl+alt+r</kbd> (<kbd>ctrl+r</kbd> on macOS). Or, look for __Requester: Run Requests__ in the command palette <kbd>shift+cmd+p</kbd> and hit Enter. A response tab will appear, with a name like __GET: /albums__.

Head to the response tab and check out the response. Hit <kbd>ctrl+alt+r</kbd> or <kbd>ctrl+r</kbd> (<kbd>ctrl+r</kbd> or <kbd>cmd+r</kbd> on macOS) to replay the request. You can edit the request, which is at the top of the file, before replaying it.

Now, go back to the requester file and highlight all 5 lines, and once again execute the requests. Nice, huh?


### Multiline Requests, Request Body, Query Params
~~~py
post(
    'httpbin.org/post',
    json={'name': 'Jimbo', 'age': 35, 'married': False, 'hobbies': ['wiki', 'pedia']}
)

get(
    'httpbin.org/get',
    params={'key1': 'value1', 'key2': 'value2'}
)
~~~

Body, Query Params, and Headers are passed to __requests__ as dictionaries. And for executing requests defined over multiple lines, you have two options:

- fully highlight one or more requests and execute them
- place your cursor inside of a request and execute it

Try it out.


## Documentation
Wanna see everything else Requester does? Detailed, [__fuzzy searchable documentation here__](https://kylebebak.github.io/Requester/).
