import psutil, time, subprocess, sys, os

# Kill all kflower backend processes
for p in psutil.process_iter():
    try:
        cl = ' '.join(p.cmdline() or [])
        if 'kflower' in cl.lower():
            print('Kill %d: %s' % (p.pid, cl[:80]))
            p.terminate()
    except: pass
time.sleep(2)

print('Starting backend (no reload, no pipe)...')
logfile = open(r'E:\kkflower\kflower-backend\_backend_out.log', 'w')
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8788'],
    cwd=r'E:\kkflower\kflower-backend',
    stdout=logfile, stderr=subprocess.STDOUT
)
print('Backend PID: %d' % proc.pid)
time.sleep(6)
logfile.flush()

# Read log
logfile.seek(0)
output = logfile.read()
print('=== BACKEND LOG ===')
print(output[-1500:])
print('=== END LOG ===')

if proc.poll() is None:
    print('Backend still running, testing HTTP...')
    import urllib.request, json, urllib.parse
    try:
        body = urllib.parse.urlencode({'username':'admin','password':'admin123','grant_type':'password'}).encode()
        resp = urllib.request.urlopen('http://localhost:8788/api/v1/auth/login', data=body, timeout=10)
        token = json.loads(resp.read())['access_token']
        print('LOGIN OK, token:', token[:20])
        
        req = urllib.request.Request('http://localhost:8788/api/v1/plugins/stats/overview')
        req.add_header('Authorization', 'Bearer ' + token)
        r = json.loads(urllib.request.urlopen(req, timeout=10).read())
        print('Stats:', json.dumps(r, ensure_ascii=False, indent=2)[:500])
    except Exception as e:
        print('HTTP Error:', e)
else:
    print('Backend died!')
