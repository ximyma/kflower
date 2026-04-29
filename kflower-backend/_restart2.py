import psutil, time, subprocess, sys, os

# Kill any existing kflower-backend processes
for p in psutil.process_iter():
    try:
        cl = ' '.join(p.cmdline() or [])
        if 'kflower' in cl.lower() and 'python' in p.name().lower():
            print(f'Killing {p.pid}: {cl[:80]}')
            p.terminate()
    except: pass
time.sleep(1)

print('Starting fresh backend...')
python_exe = sys.executable
proc = subprocess.Popen(
    [python_exe, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8788'],
    cwd=r'E:\kkflower\kflower-backend',
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)
print(f'Backend PID: {proc.pid}')
time.sleep(6)

if proc.poll() is None:
    print('Backend is running OK (pid %d)' % proc.pid)
    # Now test with a simple HTTP request
    import urllib.request, json, urllib.parse
    body = urllib.parse.urlencode({'username':'admin','password':'admin123','grant_type':'password'}).encode()
    resp = urllib.request.urlopen('http://localhost:8788/api/v1/auth/login', data=body, timeout=10)
    token = json.loads(resp.read())['access_token']
    print('LOGIN OK, token:', token[:20])
    
    req = urllib.request.Request('http://localhost:8788/api/v1/plugins/')
    req.add_header('Authorization', 'Bearer ' + token)
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    print('Plugins:', r.get('total', len(r.get('data',[]))), 'found')
    print('First:', r.get('data',[{}])[0].get('display_name','?'))
else:
    output = proc.stdout.read()
    print('Backend died! Output:', output[:1000])
