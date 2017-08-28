# flake8: noqa
###env
base_url = 'http://127.0.0.1:8000/get'
###env

requests.post('http://127.0.0.1:8000/post')
get('127.0.0.1:8000/get')

requests.get(base_url, params={'key1': 'value1'})
requests.post('http://127.0.0.1:8000/anything')
