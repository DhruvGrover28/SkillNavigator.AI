import requests
import json
base='http://127.0.0.1:8000'
print('Registering test user...')
reg = requests.post(base+'/api/user/register', json={'name':'Smoke Tester','email':'smoketest@example.com','password':'StrongPass!123','confirm_password':'StrongPass!123','terms':True})
print('status', reg.status_code)
print(reg.text)
try:
    token = reg.json().get('token')
except Exception:
    token = None
if not token:
    # Try logging in if registration returned existing user
    login = requests.post(base+'/api/user/login', json={'email':'smoketest@example.com','password':'StrongPass!123'})
    try:
        token = login.json().get('token')
    except Exception:
        token = None

if token:
    headers={'Authorization':f'Bearer {token}'}
    print('\nCalling /api/jobs/')
    r = requests.get(base+'/api/jobs/', headers=headers)
    print(r.status_code, len(r.text))
    print('/api/health ->', requests.get(base+'/api/health').json())
    print('/api/supervisor/status ->', requests.get(base+'/api/supervisor/status', headers=headers).status_code)
else:
    print('No token received; cannot test auth endpoints')
