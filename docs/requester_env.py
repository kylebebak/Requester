base_url = 'https://jsonplaceholder.typicode.com'

import requests
jar = requests.cookies.RequestsCookieJar()
jar.set('tasty_cookie', 'yum', domain='httpbin.org', path='/cookies')
