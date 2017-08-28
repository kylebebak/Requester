# flake8: noqa
###env
import requests

s = requests.Session()
s.get('http://127.0.0.1:8000/cookies/set?k0=v0', timeout=5)
s.headers.update({'X-Test': 'true'})
###env

s.get('http://127.0.0.1:8000/cookies/set?k1=v1', allow_redirects=False)
