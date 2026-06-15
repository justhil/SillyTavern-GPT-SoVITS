# -*- coding: utf-8 -*-
import os, paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("107.173.140.30", username="root", password=os.environ["GENIE_VPS_PASS"], timeout=30, allow_agent=False, look_for_keys=False)
for cmd in [
    "docker ps -a --format '{{.Names}}' | grep -iE 'silly|luker|st'",
    "docker network inspect docker_default --format '{{range .Containers}}{{.Name}} {{end}}'",
    "docker inspect luker --format '{{json .HostConfig.PortBindings}}'",
    "head -5 /www/st/docker/extensions/SillyTavern-GPT-SoVITS/index.js",
    "grep -n resolveManagerBaseUrl /www/st/docker/extensions/SillyTavern-GPT-SoVITS/index.js | head -3",
]:
    print(">>>", cmd)
    _, o, _ = c.exec_command(cmd, timeout=60)
    print(o.read().decode("utf-8", errors="replace"))
c.close()