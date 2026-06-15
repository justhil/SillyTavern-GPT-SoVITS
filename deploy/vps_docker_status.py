# -*- coding: utf-8 -*-
import os, sys, paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
host = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
c.connect(host, username="root", password=os.environ["GENIE_VPS_PASS"], timeout=30, allow_agent=False, look_for_keys=False)
_, o, _ = c.exec_command(
    "cd /www/SillyTavern-GPT-SoVITS && bash deploy/vps-stop-genie-container.sh; "
    "systemctl is-active genie-tts; curl -sf -o /dev/null -w 'genie:%{http_code}\\n' http://127.0.0.1:8429/docs; "
    "docker ps -a --format '{{.Names}} {{.Status}}' | grep -E 'tts-manager|genie|st-gateway' || true; "
    "curl -sf http://127.0.0.1:46939/tts-mw/ping; echo",
    timeout=120,
)
sys.stdout.buffer.write(o.read())
c.close()