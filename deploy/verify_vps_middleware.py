# -*- coding: utf-8 -*-
import os
import paramiko

HOST = os.environ.get("GENIE_VPS_HOST", "107.173.140.30")
PASS = os.environ.get("GENIE_VPS_PASS", "")


def run(c, cmd):
    print(">>>", cmd)
    _, o, e = c.exec_command(cmd, timeout=60)
    out = o.read()
    err = e.read()
    print(out.decode("utf-8", errors="replace"))
    if err:
        print("stderr:", err.decode("utf-8", errors="replace")[:300])


def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if not PASS:
        raise SystemExit("Set GENIE_VPS_PASS")
    c.connect(
        HOST,
        username="root",
        password=PASS,
        timeout=30,
        allow_agent=False,
        look_for_keys=False,
    )
    run(c, "systemctl is-active genie-tts sillytavern-tts-manager")
    run(c, "curl -s http://127.0.0.1:3000/ping")
    run(c, "curl -s http://127.0.0.1:3000/api/genie/status")
    run(c, "ls /www/SillyTavern-GPT-SoVITS/MyCharacters/墨白/reference_audios/Chinese/emotions/*.wav 2>/dev/null | wc -l")
    run(c, "cat /www/SillyTavern-GPT-SoVITS/genie_character_models.json")
    run(c, "grep genie_host /www/SillyTavern-GPT-SoVITS/system_settings.json")
    run(c, "cat /www/SillyTavern-GPT-SoVITS/character_mappings.json 2>/dev/null || echo '{}'")
    run(c, "curl -s -o /dev/null -w 'public_3000:%{http_code}' http://127.0.0.1:3000/ping; echo")
    c.close()


if __name__ == "__main__":
    main()