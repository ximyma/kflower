import psutil, os

killed_any = False
for p in psutil.process_iter():
    try:
        cl = ' '.join(p.cmdline() or [])
        if 'kflower' in cl.lower() and p.pid != os.getpid():
            print('Kill PID %d: %s' % (p.pid, cl[:100]))
            p.terminate()
            killed_any = True
    except: pass

if not killed_any:
    print('No kflower processes found')

# Also check what's on port 8788
print('\nPort 8788:')
for conn in psutil.net_connections():
    if conn.laddr.port == 8788:
        try:
            proc = psutil.Process(conn.pid)
            print('  PID %d (%s): %s' % (conn.pid, proc.name(), ' '.join(proc.cmdline()[:3])))
        except:
            print('  PID %d: unknown' % conn.pid)
