# genie-tts 容器 pip 失败（jieba_fast / gcc）

## 原因

`docker-compose.stack.yml` 里若走 `pip install genie-tts`，会编译 `jieba_fast`，`python:3.11-slim` 没有 `gcc`，必然失败。

## 正确做法（二选一）

### A. 推荐：Genie 留在宿主机，只 Docker 中间件

```bash
systemctl start genie-tts
cd /www/SillyTavern-GPT-SoVITS
docker compose -f docker-compose.stack.host-genie.yml up -d --build
docker compose -f docker-compose.gateway.yml up -d
```

`tts-manager` 通过 `http://172.17.0.1:8000` 访问宿主机 Genie。

### B. Genie 也进 Docker，但必须已有 `/www/genie/venv`

```bash
# 宿主机必须先有 venv + run_server.py（原 systemd 安装）
ls -l /www/genie/venv/bin/python /www/genie/run_server.py
docker compose -f docker-compose.stack.yml up -d
```

容器**只**执行 `venv/bin/python run_server.py`，**不会**再 pip install。

## 验证

```bash
curl http://127.0.0.1:8000/docs
docker exec tts-manager python3 -c "import urllib.request; print(urllib.request.urlopen('http://genie-tts:8000/docs').status)"  # 方案 B
# 或方案 A: curl http://172.17.0.1:8000/docs
```