import psutil, time, subprocess, sys, os

# Kill any existing kflower-backend processes
killed = []
for p in psutil.process_iter():
    try:
        cl = ' '.join(p.cmdline() or [])
        name = p.name()
        if 'kflower' in cl.lower() and 'python' in name.lower():
            print(f'Killing {p.pid}: {cl[:80]}')
            p.terminate()
            killed.append(p.pid)
    except: pass
time.sleep(1)

print('Starting fresh backend...')
proc = subprocess.Popen(
    [sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8788', '--log-level', 'info'],
    cwd=r'E:\kkflower\kflower-backend',
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
)
print(f'Backend PID: {proc.pid}')
time.sleep(5)

# Check if still alive and capture initial output
if proc.poll() is None:
    print('Backend still running - GOOD')
else:
    output = proc.stdout.read()
    print(f'Backend died! Output:\n{output[-800:]}')
