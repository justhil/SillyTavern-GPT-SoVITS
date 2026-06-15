# -*- coding: utf-8 -*-
import os
import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
PASS = os.environ.get("GENIE_VPS_PASS", "")


def run(c, cmd):
    print(">>>", cmd)
    _, o, e = c.exec_command(cmd, timeout=60)
    out = o.read().decode("utf-8", errors="replace")
    err = e.read().decode("utf-8", errors="replace")
    if out:
        print(out)
    if err.strip():
        print("stderr:", err[:500])


def main():
    if not PASS:
        raise SystemExit("GENIE_VPS_PASS")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    cmds = [
        "ss -tlnp | grep -E ':80|:443|:8000|:8080|:3000|:3001|:5173|:7860' || ss -tlnp",
        "docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Ports}}\t{{.Status}}' 2>/dev/null",
        "docker compose ls 2>/dev/null; ls -la /www /opt /root 2>/dev/null | head -30",
        "find /www /opt /root -maxdepth 3 -iname '*silly*' -o -iname '*tavern*' -o -iname '*luker*' 2>/dev/null | head -40",
        "systemctl list-units --type=service --state=running 2>/dev/null | grep -iE 'nginx|silly|tavern|docker' || true",
        "nginx -v 2>&1; ls -la /etc/nginx/sites-enabled/ 2>/dev/null; grep -r listen /etc/nginx/sites-enabled/ /etc/nginx/conf.d/ 2>/dev/null | head -20",
        "cat /www/SillyTavern-GPT-SoVITS/system_settings.json 2>/dev/null | head -5",
    ]
    for cmd in cmds:
        run(c, cmd)
    c.close()


if __name__ == "__main__":
    main()