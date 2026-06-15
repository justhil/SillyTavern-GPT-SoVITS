# Cloudflare 隧道（Luker + TTS 中间件）

## 重要：不用新开一条隧道

服务器上**已经在跑**：

```text
容器名: cloudflared-sillytavern
目录:   /opt/cloudflared/docker-compose.yml
```

你再执行一次 `docker run ... --token ...` 会 **重复连接同一条隧道**，容易冲突。**不要**再开第二个。

隧道 ID（从 token 里）：`da6f8a33-fdc1-4336-b8cd-74531fa2ce20`

---

## 你要做的事（网页点几下）

用 **Cloudflare 控制台** 给这条隧道加「公网主机名」，不用改 token、不用记 ingress 语法。

### 1. 登录

1. 打开 https://one.dash.cloudflare.com/
2. 左侧 **Networks** → **Connectors** → **Cloudflare Tunnels**（或 Zero Trust → Networks → Tunnels）
3. 找到状态为 **Healthy** 的那条（名称可能叫 sillytavern 或你的隧道名）→ 点 **Configure**

### 2. 加 TTS 中间件（推荐）

**Public Hostname** → **Add a public hostname**：

| 字段 | 填什么 |
|------|--------|
| Subdomain | `tts` |
| Domain | `justhil.uk` |
| Type | HTTP |
| URL | `172.17.0.1:3000` |

说明：cloudflared 在 Docker 里，访问宿主机上的 `manager.py` 用 **172.17.0.1**（Linux 默认 docker0 网关）。

保存后等 1～2 分钟，浏览器测：

```text
https://tts.justhil.uk/ping
```

应返回：`{"ok":true,"service":"sillytavern-gpt-sovits-manager",...}`

### 3. 确认酒馆（已有）

应有一条：

| Subdomain | Domain | URL |
|-----------|--------|-----|
| `st` | `justhil.uk` | `luker:2345` 或 `http://luker:2345` |

cloudflared 与 **luker** 同在 `docker_default` 网络，用容器名 **luker** 即可。

若没有或指向 `sillytavern`，改成 **luker:2345**。

### 4. 酒馆扩展里填什么

```text
https://tts.justhil.uk
```

**不要**填 `http://107.173.140.30:3000`（HTTPS 酒馆会被浏览器拦）。

扩展里点 **「清除配置，自动检测」** 或手动保存上面地址后 **强刷**（Ctrl+F5）。

---

## 本地 config.yml 和面板谁说了算？

若隧道是 **Remotely managed**（用 token / Zero Trust 创建），**公网路由以 Cloudflare 网页配置为准**，本机 `/opt/cloudflared/config.yml` 里的 `ingress` 可能被忽略。

所以：**一定要在网页里加 `tts.justhil.uk`**，不要只改服务器上的 yml。

---

## 服务器上常用命令（SSH）

```bash
# 看隧道容器
docker ps | grep cloudflared

# 重启隧道（改完面板后一般不用）
cd /opt/cloudflared && docker compose restart

# 中间件
systemctl status sillytavern-tts-manager
curl http://127.0.0.1:3000/ping
```

---

## 安全

- **不要把 tunnel token 写进 Git、群聊、截图。**
- 若 token 已泄露，Cloudflare 隧道页面 **Rotate token**，并更新 `/opt/cloudflared/docker-compose.yml` 里的 `TUNNEL_TOKEN`，再 `docker compose up -d`。

---

## 可选：只用 IP:46938 访问酒馆（无 HTTPS）

本机映射：`127.0.0.1:46938` → luker。公网若没暴露 46938，仍应用 **st.justhil.uk**。

此方式扩展中间件仍建议用 **https://tts.justhil.uk**，与酒馆是否 HTTPS 无关。