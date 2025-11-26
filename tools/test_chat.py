import requests
r = requests.post('http://127.0.0.1:5000/chat', json={'message': 'hello from test script! '})
print('status', r.status_code)
print('json', r.json())
