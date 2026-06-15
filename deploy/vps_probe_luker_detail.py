# -*- coding: utf-8 -*-
import os
import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
PASS = os.environ.get("GENIE_VPS_PASS", "")


def run(c, cmd):
    print(">>>", cmd)
    _, o, e = c.exec_command(cmd, timeout=90)
    print(o.read().decode("utf-8", errors="replace")[:8000])
    err = e.read().decode("utf-8", errors="replace")
    if err.strip():
        print("stderr:", err[:400])


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    cmds = [
        "cat /www/st/luker/Luker/docker-compose.yml",
        "docker inspect luker --format '{{json .NetworkSettings.Ports}}'",
        "docker inspect luker --format '{{range .Config.Env}}{{println .}}{{end}}' | head -30",
        "ls -la /www/st/luker/Luker/data 2>/dev/null | head -15",
        "find /www/st/luker -name 'extensions' -type d 2>/dev/null | head -10",
        "docker exec luker sh -c 'ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null' | head -15",
        "grep -r 'luker\\|46938\\|2345\\|silly' /opt/1panel/apps/openresty 2>/dev/null | head -25",
        "ls /opt/1panel/apps/openresty/openresty/conf/conf.d/ 2>/dev/null; ls /www/sites 2>/dev/null | head -20",
        "find /opt/1panel -name '*.conf' -path '*proxy*' 2>/dev/null | head -15",
        "docker logs cloudflared-sillytavern 2>&1 | tail -8",
        "ps aux | grep -E '8000|3335063' | head -5",
    ]
    for cmd in cmds:
        run(c, cmd)
        print("---")
    c.close()


if __name__ == "__main__":
    main()