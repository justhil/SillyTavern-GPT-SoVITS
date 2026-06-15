# Docker 栈（与 Luker 同网）

## 架构

```text
docker_default 网络
  luker:2345          ← 酒馆
  tts-manager:3000    ← 中间件（挂载 /www/SillyTavern-GPT-SoVITS）
  genie:8000          ← Genie（挂载 /www/genie）
  cloudflared         ← 公网入口
```

- 中间件环境变量 `GENIE_HOST=http://genie:8000`（容器名访问，不经宿主机端口）
- 数据仍在宿主机目录，容器只映射卷

## 部署

```bash
cd /www/SillyTavern-GPT-SoVITS
git pull
bash deploy/vps-docker-stack.sh
```

或：

```bash
docker compose -f docker-compose.stack.yml up -d --build
```

## Cloudflare（主机名路由）

| 主机名 | 服务 URL |
|--------|----------|
| `st.justhil.uk` | `http://luker:2345` |
| `tts.justhil.uk` | **`http://tts-manager:3000`** |

不要用 `172.17.0.1:3000`。

## 酒馆扩展

```text
https://tts.justhil.uk
```

## 常用命令

```bash
docker compose -f /www/SillyTavern-GPT-SoVITS/docker-compose.stack.yml logs -f tts-manager
docker compose -f /www/SillyTavern-GPT-SoVITS/docker-compose.stack.yml restart tts-manager genie
curl http://127.0.0.1:3000/ping
```