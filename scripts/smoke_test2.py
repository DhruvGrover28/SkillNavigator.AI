import requests
base='http://127.0.0.1:8000'
login = requests.post(base+'/api/user/login', json={'email':'smoketest@example.com','password':'StrongPass!123'})
print('login status', login.status_code)
try:
    token = login.json().get('token')
except:
    token = None
print('token present', bool(token))
if token:
    headers={'Authorization':f'Bearer {token}'}
    r = requests.get(base+'/api/supervisor/status', headers=headers)
    print('supervisor/status', r.status_code)
    try:
        print(r.json())
    except Exception as e:
        print('json error', e, r.text)
else:
    print('no token')
