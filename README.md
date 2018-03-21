# Requester: HTTP Client for Humans

![License](https://camo.githubusercontent.com/890acbdcb87868b382af9a4b1fac507b9659d9bf/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)
[![Build Status](https://travis-ci.org/kylebebak/Requester.svg?branch=master)](https://travis-ci.org/kylebebak/Requester)
[![Coverage Status](https://coveralls.io/repos/github/kylebebak/Requester/badge.svg?branch=master)](https://coveralls.io/github/kylebebak/Requester?branch=master)
[![Join the chat at https://gitter.im/kylebebak/Requester](https://badges.gitter.im/kylebebak/Requester.svg)](https://gitter.im/kylebebak/Requester?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


__Requester__ is a modern, team-oriented HTTP client for Sublime Text 3 that combines features of apps like Postman, Paw and HTTPie with rock-solid usability and the secret sauce of Requests. 🌟

- [Super classy syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + Easily set request body, query params, custom headers, cookies
  + Support for sessions, authentication
  + Forms and file uploads, Wget-style downloads
  + HTTPS, proxies, redirects, and more
- Intuitive, modern UX
  + Define [__environment variables__](http://requester.org/#environment-variables) with regular Python code
  + Execute requests and display responses in parallel, [__or chain requests__](http://requester.org/#chaining-by-reference)
  + Edit and replay requests from individual response tabs, page through past requests
    * [__Explore hyperlinked APIs__](http://requester.org/#explore-hyperlinked-apis-hateoas) from response tabs
  + Fuzzy searchable [__request collections and request history__](http://requester.org/#navigation-and-history)
  + Formatted, colorized output with automatic syntax highlighting
  + Clear error handling and error messages
  + [__Full GraphQL support__](http://requester.org/#graphql)
- Built for teams
  + Version and share requests however you want (Git, GitHub, etc)
  + Export requests to cURL or HTTPie, import requests from cURL
  + Lightweight, integrated test runner with support for JSON Schema
    * [__Export Requester tests to runnable test script__](http://requester.org/#export-tests-to-runnable-script)
  + [AB-style](https://httpd.apache.org/docs/2.4/programs/ab.html) benchmarking tool
  + Runs on Linux, Windows and macOS/OS X
- [__Highly extensible__](http://requester.org/#import-any-python-package-with-requester)

---

If you're looking for an HTTP client you should try Requester __even if you've never used Sublime Text__.


## Installation
1. Download and install [Sublime Text 3](https://www.sublimetext.com/3).
2. Install [Package Control for Sublime Text](https://packagecontrol.io/).
3. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
4. Search for __Requester__ (not ~~Http Requester~~) and install it.
5. __If you're seeing errors__ every time you run a request, this probably means the __requests__ dependency wasn't installed successfully. To fix this, look for __Package Control: Satisfy Dependencies__ in the command palette, run it, and restart Sublime Text.


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
Wanna see everything else Requester does? Detailed, [__fuzzy searchable documentation here__](http://requester.org).


## Why Requester?
Requester combines features from applications like Postman, Paw, Insomnia and HTTPie with the elegance and power of Requests and rock-solid UX of Sublime Text.

Requester leans on [Requests](http://docs.python-requests.org/en/master/user/quickstart/) as much as possible. This means Requester does most anything Requests does, which means it does most anything you need to explore, debug, and test a modern API.

It also means Requester uses an extensively documented, battle-tested library famed for its beauty. If you don't know how to do something with Requester, there are thousands of blog posts, articles and answers on Stack Overflow that explain how to do it.

Apart from being feature-rich, __Requester is built for speed and simplicity__. I was a Postman user before writing Requester, and I got tired of, for example, having to click in 4 places to add or change an env var. With Requester you might have to move your cursor up a few lines.

Request navigation and history, which use Sublime Text's [blistering fast fuzzy match](https://www.reddit.com/r/programming/comments/4cfz8r/reverse_engineering_sublime_texts_fuzzy_match/), are especially powerful. Jump between requests and request groups in your requester file. Hop between open response tabs. Find the exact version of a request you executed a week ago.  It's all lightning fast.

The paid collaboration features of HTTP client apps, such as sharing and versioning, are not only free in Requester, they're better. Requester works with text files, and as good as the developers at Postman and Paw are, they don't beat GitHub at collaboration, and they don't beat Git at version control.

Need to share requests with someone who doesn't use Requester? Exporting your requests to cURL or HTTPie takes a few seconds. Ditto with importing requests from cURL, which means it's trivial to grab AJAX requests sent by your browser and pull them into Requester.

Requester is cross-platform and built for teams. If you debug web APIs for work or for fun, try it. __Try it even if you don't use Sublime Text__. You'll have to switch between two text editors, but you already have to switch between your editor and your HTTP client, and I'm betting you'll like Requester more. ✨✨


[![Requester](https://raw.githubusercontent.com/kylebebak/Requester/master/assets/requester.png)](https://www.youtube.com/watch?v=kVO5AWIsmF0 "Requester")
