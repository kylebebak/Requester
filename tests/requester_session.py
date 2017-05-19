###env
import requests

s = requests.Session()
s.get('http://httpbin.org/cookies/set?k0=v0', timeout=5)
s.headers.update({'X-Test': 'true'})
###env

s.get('http://httpbin.org/cookies/set?k1=v1', allow_redirects=False)
