# -*- coding: utf-8 -*-
import os, paramiko
HOST, PASS = "107.173.140.30", os.environ.get("GENIE_VPS_PASS", "")

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    cmds = [
        "find /opt/1panel/www/sites -iname '*silly*' -o -iname '*st.just*' 2>/dev/null",
        "ls /opt/1panel/www/sites/ 2>/dev/null",
        "grep -r '46938\\|2345\\|luker\\|sillytavern' /opt/1panel/www/sites 2>/dev/null | head -30",
        "docker network ls; docker inspect luker --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}} {{end}}'",
        "docker ps --filter name=silly --format '{{.Names}} {{.Ports}}'",
        "cat /opt/cloudflared/docker-compose.yml 2>/dev/null; cat /opt/cloudflared/config.yml 2>/dev/null | head -40",
    ]
    for cmd in cmds:
        print(">>>", cmd)
        _, o, _ = c.exec_command(cmd, timeout=60)
        print(o.read().decode("utf-8", errors="replace")[:6000])
        print("---")
    c.close()

if __name__ == "__main__":
    main()