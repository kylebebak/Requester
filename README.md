# Requester
A __simple__ and __powerful__ Sublime Text 3 HTTP client built on top of [Requests](http://docs.python-requests.org/en/master/). Like Requests, it's intuitive, expressive, and __extremely easy to use__.

Requester is like [Postman](https://www.getpostman.com/) for your text editor. Get __environment variables__, __concurrent requests__, __multiple, editable response tabs__ and the __famously elegant syntax__ of Requests, without neutering your keyboard.


## Features
- [Requests' beautiful syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + easily set request body, custom headers, cookies, query params, etc
- environment variables
  + separate env vars for each project
  + define env vars using Python code
- execute requests and display responses in parallel
- display responses in response tabs
  + edit and replay individual requests from response tabs
  + view response metadata, headers, content
  + sensible tab names make navigation easy
- automatic response syntax highlighting
- JSON response pretty printing
- comprehensive error handling and clear error messages


## Requester How To
close all tabs
timeout
env_var_file
redirect history
requests open in same tab


## Why Requester?
There are already several HTTP clients for Sublime Text, but they lack many of the following:

- well-documented syntax
- intuitive syntax
- environment variables
- multiple response tabs
- editable response tabs
- automatic syntax highlighting

Postman addresses these concerns, which is why so many web developers use it. But using an app like Postman instead of a text editor has its own disadvantages:

- you're constantly switching contexts between your HTTP client and your code
- manipulating requests requires lots of point and click
  + your keyboard wizardry is suddenly worthless 
- requests are stored in a proprietary format
  + they're difficult to share
  + they can't be added to version control

Requester is built from the ground up to give you the best of both worlds.


## Installation
1. Install [Package Control](https://packagecontrol.io/) if you don't have it already.
2. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
3. Search for __Requester__ (not ~~Http Requester~~) and install it.
