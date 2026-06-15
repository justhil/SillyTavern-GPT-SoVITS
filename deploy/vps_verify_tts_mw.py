# -*- coding: utf-8 -*-
import os, paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
host = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
c.connect(host, username="root", password=os.environ["GENIE_VPS_PASS"], timeout=30, allow_agent=False, look_for_keys=False)
cmds = [
    "cat /opt/cloudflared/config.yml",
    "docker exec cloudflared-sillytavern wget -qO- http://172.17.0.1:3000/ping 2>&1",
    "curl -sk https://st.justhil.uk/tts-mw/ping",
    "head -3 /www/st/docker/extensions/SillyTavern-GPT-SoVITS/index.js",
    "wc -l /www/st/docker/extensions/SillyTavern-GPT-SoVITS/index.js",
]
for cmd in cmds:
    print(">>>", cmd)
    _, o, _ = c.exec_command(cmd, timeout=45)
    print(o.read().decode("utf-8", errors="replace")[:1500])
    print("---")
c.close()