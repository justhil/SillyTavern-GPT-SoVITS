# 部署文档索引

| 文档 | 说明 |
|------|------|
| **[VPS-RUNBOOK.md](./VPS-RUNBOOK.md)** | **总览**：请求链路、端口、脚本、敏感信息审查 |
| [VPS-STATUS-SNAPSHOT.md](./VPS-STATUS-SNAPSHOT.md) | 2026-06-15 状态快照（不含训练） |
| [DOCKER-GENIE-FIX.md](./DOCKER-GENIE-FIX.md) | 为何 Genie 用 systemd 而非 Docker |
| [DOCKER-STACK.md](./DOCKER-STACK.md) | Compose 栈说明（部分历史端口，以 RUNBOOK 8429/46939 为准） |
| [LUKER-ST.md](./LUKER-ST.md) | Luker 与扩展 |
| [CLOUDFLARE-TUNNEL.md](./CLOUDFLARE-TUNNEL.md) | 可选 CF 隧道 |
| [.env.stack.example](./.env.stack.example) | `TTS_MW_API_KEY` 模板（复制为 `deploy/.env`，勿提交） |

**快速部署（VPS）**

```bash
cd /www/SillyTavern-GPT-SoVITS
git pull https://github.com/justhil/SillyTavern-GPT-SoVITS.git main
bash deploy/vps-deploy-st-gateway.sh
# 或 Genie 端口异常时：
bash deploy/vps-fix-genie-8429-now.sh
```