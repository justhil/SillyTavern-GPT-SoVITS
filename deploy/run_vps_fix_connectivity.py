# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path
import paramiko
HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
USER = os.environ.get("GENIE_VPS_USER", "root")
PASS = os.environ.get("GENIE_VPS_PASS", "")
SCRIPT = Path(__file__).parent / "vps-fix-connectivity.sh"

def main():
    if not PASS:
        sys.exit("GENIE_VPS_PASS")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=30, allow_agent=False, look_for_keys=False)
    body = SCRIPT.read_text(encoding="utf-8")
    sftp = c.open_sftp()
    remote = "/tmp/vps-fix-connectivity.sh"
    with sftp.file(remote, "w") as f:
        f.write(body)
    sftp.chmod(remote, 0o755)
    sftp.close()
    _, o, e = c.exec_command(f"bash {remote}", get_pty=True, timeout=300)
    for line in iter(o.readline, ""):
        print(line, end="")
    print(e.read().decode(errors="replace"))
    c.close()

if __name__ == "__main__":
    main()