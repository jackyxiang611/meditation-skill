---
name: meditation-skill
description: |
  端到端生成个性化冥想音频（只输出最终音频文件）：从用户上下文推断目标（助眠/减压/焦虑/专注/静心）→ 生成逐句引导语脚本（含停顿/送钵标记）→ 逐句调用 TTS 合成旁白并插入停顿/送钵 → 按旁白时长循环/截断背景音乐 → ffmpeg 混音导出 mp3。
  用户只要提到“冥想音频/助眠/放松/焦虑/专注/背景音乐/送钵/留白/合成/ffmpeg/TTS”，就使用此 Skill。
compatibility:
  requires:
    - ffmpeg (installed locally, available in PATH)
    - node (optional; used for picking music from music.json)
    - Python 3.12+ (for scripts)
---

# Meditation Skill（发布版：只输出最终音频）

目标：生成一条可直接收听的冥想音频（mp3）。

- 默认 **只交付最终成品**：`outputs/meditation-*.mp3`
- 中间产物（脚本、分句音频、临时 wav）保存在 `tmp/`，不在对话里展示

> 如果需要排查问题，可以临时打开“调试输出”（见下方 Debug）。

---

## 目录结构（建议保持不变）
- `assets/audio/music.sample.json`：示例背景音乐映射（仓库内置）
- `assets/audio/music.local.json`：你本机的完整映射（不提交）
- `assets/audio/sample-bg.mp3`：示例背景音乐（仓库内置）
- `assets/audio/song.mp3`：送钵音（约 25 秒/次）
- `assets/audio/silence_1s.mp3`：1 秒留白音
- `scripts/`：合成脚本
- `tmp/`：临时文件（不提交）
- `outputs/`：最终输出（可选择提交 sample，也可不提交）

---

## 配置（重要，准备分享到 GitHub）
### 1) 机密信息不要提交
本 Skill 使用 `.env` 存放密钥（不要提交到 GitHub）：
- 已在 `.gitignore` 中忽略 `.env`
- 提供 `.env.example` 作为模板

### 2) 火山 TTS（优先）
复制并编辑：
```bash
cp .env.example .env
```
在 `.env` 里填写（至少两项）：
- `VOLC_TTS_APPID=...`
- `VOLC_TTS_TOKEN=...`

推荐配置：
- `VOLC_TTS_VOICE_TYPE=BV700_V2_streaming`
- `VOLC_TTS_STYLE=yoga`
- `VOLC_TTS_SPEED_RATIO=0.7`（越小越慢）
- `VOLC_TTS_MAX_CHARS=150`（防止 exceed max len limit）

> 注意：长文本会被自动分段合成再拼接。

### 3) TTS 保底方案（火山不可用时）
当火山接口不可用（网络/证书/鉴权/限流等），应自动切换为 OpenClaw 内置 `tts` 工具逐句合成。

实现约定：
- “逐句合成 + 插入停顿/送钵 + 拼接时间轴”的策略不变
- 只是把每句的 TTS 引擎从 `scripts/tts_volc.py` 换成内置 `tts`

---

## 核心规则（体验一致性）
1) **逐句脚本**：引导语必须按“句”生成，每句一行。
2) **最小停顿**：任何两个 item（引导语句子 / 送钵 / 停顿段）之间，必须至少 **1 秒留白**。
   - 不允许两句连读
   - 不允许引导语与送钵无缝衔接
3) **背景时长**：以“旁白时间轴”的总时长为准，背景音乐循环/截断到同长。
4) **时长预期**：用户给的 `duration_min` 是目标时长；由于停顿与送钵存在，最终音频可能偏离目标。
   - 如果需要严格卡时长：后续可做“PAUSE 自动缩放”（根据预算压缩/扩展 pause 秒数）。

---

## 工作流（发布版）
你在内部按下面步骤完成，但**对外只返回最终 mp3 路径**。

### Step A：生成逐句引导语脚本（含标记）
保存到：`tmp/script.txt`

脚本格式：每行一个 item
- 普通引导语句子：直接写一句话（逐句 TTS）
- 停顿：`[[PAUSE:seconds]]`
- 送钵：`[[BOWL]]`

### Step B：逐句 TTS + 插入停顿/送钵 → 旁白时间轴
生成：`tmp/voiceover_timeline.wav`

使用：
- `scripts/compose_voiceover.py`

### Step C：选择背景音乐并对齐
- 读取 `assets/audio/music.json`
- 可用 `scripts/pick_music.js` 按 goal 选曲
- 背景音不足则循环，过长则截断到旁白时长

### Step D：混音导出
导出：`outputs/meditation-YYYYMMDD-HHMM-<goal>.mp3`

ffmpeg 混音模板（示例，可按需微调人声/背景比例）：
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "tmp/voiceover_timeline.wav")
FADE_OUT_D=8
FADE_OUT_START=$(python3 - <<PY
print(max(0, float("$DUR")-$FADE_OUT_D))
PY
)

ffmpeg -y \
  -i "tmp/voiceover_timeline.wav" \
  -stream_loop -1 -i "tmp/bg.wav" \
  -filter_complex "\
    [0:a]volume=-2dB[vo];\
    [1:a]volume=-14dB[bg];\
    [bg][vo]sidechaincompress=threshold=0.03:ratio=8:attack=10:release=500[bgduck];\
    [bgduck][vo]amix=inputs=2:duration=first:dropout_transition=2[mix];\
    [mix]afade=t=in:st=0:d=4,afade=t=out:st=${FADE_OUT_START}:d=${FADE_OUT_D}[aout]\
  " \
  -map "[aout]" -shortest \
  -c:a libmp3lame -b:a 192k \
  "outputs/meditation.mp3"
```

---

## Debug（默认关闭）
如果需要排查，可额外导出：
- `outputs/voiceover-*.wav`
- `outputs/background-*.wav`

发布到 GitHub 时建议默认不生成或不提交这些 debug 文件。
