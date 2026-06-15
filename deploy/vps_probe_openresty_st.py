# -*- coding: utf-8 -*-
import os, paramiko
HOST, PASS = "107.173.140.30", os.environ.get("GENIE_VPS_PASS", "")

def run(c, cmd):
    print(">>>", cmd)
    _, o, _ = c.exec_command(cmd, timeout=60)
    print(o.read().decode("utf-8", errors="replace")[:12000])

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    for cmd in [
        "find /www/sites /opt/1panel -name 'sillytavern.conf' 2>/dev/null",
        "find /www/sites -type f -name '*.conf' 2>/dev/null | head -20",
        "docker exec 1Panel-openresty-vYKP cat /usr/local/openresty/nginx/conf/conf.d/sillytavern.conf 2>/dev/null",
        "ls -la /www/st/docker/extensions/ 2>/dev/null | head -20",
        "curl -sI http://127.0.0.1:46938/ | head -8",
        "curl -s http://127.0.0.1:46938/ping 2>/dev/null | head -3",
    ]:
        run(c, cmd)
        print("---")
    c.close()

if __name__ == "__main__":
    main()