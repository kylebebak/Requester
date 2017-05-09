# Requester
A simple and powerful Sublime Text 3 HTTP client built on top of [Requests](http://docs.python-requests.org/en/master/). Like Requests, it's intuitive, expressive, and easy to use.

Requester is like [Postman](https://www.getpostman.com/) for your text editor. Get environment variables, concurrent requests, multiple, editable response tabs and the elegant syntax of Requests, without neutering your keyboard.


## Features
- [Requests' syntax](http://docs.python-requests.org/en/master/user/quickstart/)
  + easily set request body, custom headers, cookies, query params, etc
- Environment variables
- Execute requests and display responses in parallel
- Display responses in response tabs
  + Edit and replay individual requests from response tabs
  + View response metadata, headers, content
- Automatic response syntax highlighting and pretty printing
- Clear error handling and error messages


## Why Requester?
There are several HTTP clients for Sublime Text, but they lack many of the following:

- Well-documented, intuitive syntax
- Environment variables
- Multiple, editable response tabs
- Automatic syntax highlighting

Postman addresses these concerns, which might be why it's so popular... But using an app like Postman has its own disadvantages:

- Constantly switching contexts between HTTP client and code.
- Manipulating requests requires lots of point and click: __keyboard wizardry is worthless__.
- Requests are stored in a proprietary format: difficult to share, difficult to add to version control.

Requester is built from the ground up to give you the best of both worlds. Try it, see for yourself =)


## Installation
1. Install [Package Control](https://packagecontrol.io/) if you don't have it already.
2. Open the command palette <kbd>shift+cmd+p</kbd> and type __Package Control: Install Package__.
3. Search for __Requester__ (not ~~Http Requester~~) and install it.
