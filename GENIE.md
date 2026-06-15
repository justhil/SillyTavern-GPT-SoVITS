# Genie TTS 接入说明

中间件默认使用 **Genie TTS HTTP API**，不再依赖本机 GPT-SoVITS `9880` 与 Windows 整合包安装向导。

## 模型文件放哪

默认根目录：**插件目录下的 `MyCharacters/`**（可在 Admin → 系统设置 →「模型目录路径」改成你自己的盘符路径）。

每个角色/说话人对应**一个子文件夹**（文件夹名 = 模型包名），结构示例：

```text
MyCharacters/
  墨白/                          ← 模型文件夹名（与 genie 映射、绑定用）
    reference_audios/            ← 参考音频（必用）
      中文/
        emotions/                ← 按情绪放 wav + 同名 .txt 文案
          default_xxx.wav
          default_xxx.txt
    onnx/                        ← 可选：本机放 ONNX 时可不写 genie_character_models.json
      vits_fp32.onnx
      ...
```

**ONNX 在 VPS 上时**：中间件机器可以没有 `.onnx`，只在 `genie_character_models.json` 里写 VPS 上的绝对路径（见下）。参考音频路径必须是 **Genie 服务能读到的路径**（同机或 NFS/挂载到 Genie 容器内）。

## 怎么切换角色（酒馆）

逻辑与旧版一致，**按「酒馆角色卡名字」绑定模型文件夹**，合成时自动 `load_character` + 按情绪选参考音频。

1. 启动中间件 `manager.py`，打开 `http://localhost:3000/admin`。
2. 在 **模型管理** 里确认 `MyCharacters` 下已有对应文件夹和 `reference_audios`。
3. 在酒馆插件 UI（或扩展面板）里：**角色名 → 绑定到模型文件夹**（写入 `character_mappings.json`）。
   - 例：酒馆卡叫「墨白」→ 绑定文件夹 `墨白`。
4. 对话里该说话人的气泡会用绑定文件夹里的参考音频；换角色 = 换绑定或换说话人（多角色对话按 `data-voice-name`）。
5. Genie 侧：第一次合成某角色时会 `POST /load_character`；换情绪会 `set_reference_audio`（文案需与 wav 一致）。

多角色同屏：每个气泡的 `voice-name` 必须在 `character_mappings.json` 里有绑定，且该文件夹在 `genie_character_models.json` 或 `onnx/` 可解析。

## 配置

1. **system_settings.json**
   - `genie_host`：如 `http://127.0.0.1:8000` 或 VPS 地址
   - `tts_engine`：`genie`（默认）

2. **genie_character_models.json**（按「模型文件夹名」映射）

```json
{
  "墨白": {
    "genie_character": "墨白",
    "onnx_model_dir": "/www/genie/characters/墨白",
    "language": "zh"
  }
}
```

若未写条目，且 `base_dir/模型名/onnx/vits_fp32.onnx` 存在，则自动用文件夹名作为 `genie_character`。

3. **character_mappings.json**：酒馆角色名 → 模型文件夹（与原先一致）。

4. **参考音频**：`reference_audios` 下 wav 与对应文案需与 Genie `set_reference_audio` 的 `audio_text` 一致。

## API 流程

`load_character` → `set_reference_audio` → `POST /tts`（32kHz PCM）→ 中间件转 WAV 缓存。

## 启动

- Linux/macOS：`./start.sh`
- Windows：`start.bat`（系统 Python 3.10+，`pip install -r requirements.txt`）
- Genie 服务单独部署（VPS systemd 或本机 `Genie-TTS`）。

## 酒馆安装本仓库（justhil fork）

```bash
git clone https://github.com/justhil/SillyTavern-GPT-SoVITS.git
cd SillyTavern-GPT-SoVITS
pip install -r requirements.txt
python manager.py
```

SillyTavern 扩展里连接的是 **中间件 `http://<IP>:3000`**（`python manager.py`），**不是** Genie 的 `:8000`。

### 连不上「插件后端」时

| 填哪里 | 填什么 |
|--------|--------|
| 酒馆 TTS 面板 / 救援框 / 远程 IP | 跑 **manager.py** 的机器 IP，**只填 IP**（会自动用 **3000**） |
| Admin → 系统设置 → Genie TTS API | Genie 地址，如 `http://107.173.140.30:8000` |

若曾把 `http://107.173.140.30:8000` 填进远程 IP，请改成 **`107.173.140.30`** 或本机局域网 IP，保存刷新。