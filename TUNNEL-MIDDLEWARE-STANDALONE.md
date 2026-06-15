# 中间件独立 Docker + Cloudflare Tunnel

完整说明见本地 `docs/MIDDLEWARE-STANDALONE-TUNNEL.md`（`docs/` 已 gitignore 时仅本地保留）。

## 快速步骤

### 1. 只起中间件（与 luker 无关）

```bash
cd /www/SillyTavern-GPT-SoVITS
export TTS_ROOT=/www/SillyTavern-GPT-SoVITS GENIE_ROOT=/www/genie
docker compose -f docker-compose.middleware-standalone.yml up -d --build
```

Genie 仍用宿主机：`systemctl start genie-tts`（:8429）。

### 2. Cloudflare Tunnel 两条 Public Hostname

| 域名 | 回源 Service |
|------|----------------|
| `st.justhil.uk` | `http://luker:2345` |
| `tts.justhil.uk` | **`http://tts-manager:3000`** |

`cloudflared` 与 `tts-manager` 须同在 **`docker_default`**。

### 3. 扩展

- 酒馆：`https://st.justhil.uk/`
- 中间件：**`https://tts.justhil.uk`**（独立域名，**不要** `/tts-mw`）

### 4. 自测

```text
https://tts.justhil.uk/ping
https://tts.justhil.uk/admin/
```

### 与同源方案区别

| | 同源 st-gateway | 独立 tts 子域 |
|--|-----------------|---------------|
| 扩展 | `https://st.xxx/tts-mw` | `https://tts.xxx` |
| Tunnel | `st.xxx` → `st-gateway:80` | `tts.xxx` → `tts-manager:3000` |