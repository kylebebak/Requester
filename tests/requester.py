# flake8: noqa
###env
base_url = 'http://httpbin.org/get'
###env

requests.post('jsonplaceholder.typicode.com/albums')
get('https://jsonplaceholder.typicode.com/posts')

requests.get(base_url, params={'key1': 'value1'})
