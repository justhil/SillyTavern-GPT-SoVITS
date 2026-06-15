# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path
import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
PASS = os.environ.get("GENIE_VPS_PASS", "")
SCRIPT = Path(__file__).parent / "vps-docker-tts-stack.sh"


def main():
    if not PASS:
        sys.exit("GENIE_VPS_PASS")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username="root", password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    sftp = c.open_sftp()
    remote = "/tmp/vps-docker-tts-stack.sh"
    with sftp.file(remote, "w") as f:
        f.write(SCRIPT.read_text(encoding="utf-8"))
    sftp.chmod(remote, 0o755)
    sftp.close()
    _, o, e = c.exec_command(f"bash {remote}", get_pty=True, timeout=900)
    for line in iter(o.readline, ""):
        print(line, end="")
    sys.exit(o.channel.recv_exit_status())


if __name__ == "__main__":
    main()