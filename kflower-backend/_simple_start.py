import subprocess, sys, time, os

os.chdir(r'E:\kkflower\kflower-backend')

print('Starting uvicorn directly...')
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8788'],
    stdout=open('_out.log','w'), stderr=subprocess.STDOUT
)
print('Started PID:', proc.pid)
time.sleep(8)
print('Poll result:', proc.poll())

if proc.poll() is None:
    print('Backend running!')
    # test
    import urllib.request, json, urllib.parse
    body = urllib.parse.urlencode({'username':'admin','password':'admin123','grant_type':'password'}).encode()
    resp = urllib.request.urlopen('http://localhost:8788/api/v1/auth/login', data=body, timeout=10)
    token = json.loads(resp.read())['access_token']
    print('LOGIN OK, token:', token[:20])
    
    req = urllib.request.Request('http://localhost:8788/api/v1/plugins/stats/overview')
    req.add_header('Authorization', 'Bearer ' + token)
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    print('Stats:', json.dumps(r, ensure_ascii=False)[:300])
else:
    print('CRASHED! Log:')
    print(open('_out.log').read()[-1000:])
