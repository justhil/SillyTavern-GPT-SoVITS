# -*- coding: utf-8 -*-
"""上传 vps-setup-middleware.sh 并在 VPS 执行（需环境变量 GENIE_VPS_PASS 或 SSH 密钥）。"""
import os
import sys
from pathlib import Path

import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
USER = os.environ.get("GENIE_VPS_USER", "root")
PASS = os.environ.get("GENIE_VPS_PASS", "")
SCRIPT = Path(__file__).resolve().parent / "vps-setup-middleware.sh"


def main():
    if not SCRIPT.is_file():
        print("missing", SCRIPT)
        sys.exit(1)
    body = SCRIPT.read_text(encoding="utf-8")
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if not PASS:
        print("Set GENIE_VPS_PASS", file=sys.stderr)
        sys.exit(1)
    c.connect(
        HOST,
        username=USER,
        password=PASS,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    sftp = c.open_sftp()
    remote = "/tmp/vps-setup-middleware.sh"
    with sftp.file(remote, "w") as f:
        f.write(body)
    sftp.chmod(remote, 0o755)
    sftp.close()
    print(f"ssh {USER}@{HOST} bash {remote}")
    stdin, stdout, stderr = c.exec_command(f"bash {remote}", get_pty=True, timeout=600)
    for line in iter(stdout.readline, ""):
        print(line, end="")
    err = stderr.read().decode()
    if err:
        print(err, file=sys.stderr)
    code = stdout.channel.recv_exit_status()
    c.close()
    sys.exit(code)


if __name__ == "__main__":
    main()