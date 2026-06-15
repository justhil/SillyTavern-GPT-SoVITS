# Docker 酒馆 + 中间件

浏览器里的请求**从你家电脑发出**，不会进 SillyTavern 容器。因此：

- 容器里的 `127.0.0.1:3000` **不是**宿主机上的 `manager.py`
- 必须在酒馆扩展里填 **宿主机局域网 IP** 的 `:3000`

## 推荐架构

```
[浏览器] --http--> [宿主机:3000 manager.py] --http--> [Genie :8000]
                         ^
[SillyTavern Docker]     |（仅页面，不代理 TTS）
```

## 步骤

### 1. 宿主机跑中间件（不要只跑在容器里）

```bash
cd SillyTavern-GPT-SoVITS
pip install -r requirements.txt
python manager.py
# 监听 0.0.0.0:3000
```

宿主机浏览器应能打开：`http://127.0.0.1:3000/admin`

### 2. 查宿主机局域网 IP

- Windows：`ipconfig` → IPv4（如 `192.168.1.5`）
- Linux/Mac：`ip addr` / `ifconfig`

### 3. 酒馆扩展配置

打开 TTS 配置 → **Docker / 远程中间件** 打开 → 填：

`http://192.168.1.5:3000`（换成你的 IP）

或首次进入时底部 **🐳 Docker 酒馆** 横幅里填写并保存。

### 4. Genie

仍在 **Admin（3000）→ 系统设置 → Genie API**，例如 `http://VPS:8000`。

## 可选：中间件也 Docker（与酒馆同机）

见 `docker-compose.middleware.yml`。映射 `3000:3000` 后，扩展里填：

`http://宿主机IP:3000`（不是 `localhost` 若酒馆也在 Docker）

## 防火墙

放行宿主机 **TCP 3000**（局域网访问）。

## 检测

`curl http://宿主机IP:3000/ping` 应返回 `{"ok":true,...}`