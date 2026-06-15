# -*- coding: utf-8 -*-
import os, sys, paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("107.173.140.30", username="root", password=os.environ["GENIE_VPS_PASS"], timeout=30, allow_agent=False, look_for_keys=False)
_, o, _ = c.exec_command(
    "docker ps -a --filter name=tts-manager --filter name=genie-tts --format '{{.Names}} {{.Status}}'; "
    "cd /www/SillyTavern-GPT-SoVITS && docker compose -f docker-compose.stack.yml up -d 2>&1 | tail -20; "
    "sleep 5; docker ps --filter name=tts-manager --filter name=genie-tts; "
    "docker run --rm --network docker_default curlimages/curl -s http://tts-manager:3000/ping 2>&1 | head -3",
    timeout=300,
)
sys.stdout.buffer.write(o.read())
c.close()