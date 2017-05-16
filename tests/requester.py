###env
base_url = 'http://httpbin.org/get'
###env

get('https://jsonplaceholder.typicode.com/posts')
post('https://jsonplaceholder.typicode.com/posts')

requests.get('https://jsonplaceholder.typicode.com/albums')
requests.post('https://jsonplaceholder.typicode.com/albums')

requests.get(base_url, params={'key1': 'value1', 'key2': 'value2'})
