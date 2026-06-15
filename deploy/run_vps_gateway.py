# -*- coding: utf-8 -*-
import os, sys
import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
PASS = os.environ.get("GENIE_VPS_PASS", "")
TTS_ROOT = os.environ.get("TTS_ROOT", "/www/SillyTavern-GPT-SoVITS")


def main():
    if not PASS:
        sys.exit("GENIE_VPS_PASS")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    cmd = (
        f"cd {TTS_ROOT} && git pull origin main && bash deploy/vps-deploy-st-gateway.sh"
    )
    _, o, _ = c.exec_command(cmd, get_pty=True, timeout=300)
    out = o.read().decode("utf-8", errors="replace")
    sys.stdout.buffer.write(out.encode("utf-8", errors="replace"))
    c.close()


if __name__ == "__main__":
    main()