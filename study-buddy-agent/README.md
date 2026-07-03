# Study Buddy - Multi-Agent Revision Assistant

A terminal-based study assistant built with [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/). It helps students turn homework, deadlines, lecture PDFs, and revision goals into study plans, revision notes, and daily to-do lists.

## Features

- Multi-agent workflow: Coordinator, Planner, Research, and Reminder agents
- Local MCP filesystem server for reading/writing `study_plan.md`
- PDF text extraction from `study_materials/` using `pypdf`
- Supports Gemini, Vertex AI, or OpenRouter (via LiteLLM)

## Quick Start

### Requirements

- Python 3.12+
- An API key from one of:
  - [OpenRouter](https://openrouter.ai/) (recommended for demos / Hong Kong users)
  - [Google AI Studio](https://aistudio.google.com/)
  - Google Cloud Vertex AI

### Installation

```powershell
git clone https://github.com/YOUR_USERNAME/study-buddy-agent.git
cd study-buddy-agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

If PowerShell blocks script execution:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Configure `.env`

Copy `.env.example` to `.env`, then choose one provider.

**OpenRouter (recommended):**

```env
STUDY_BUDDY_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
STUDY_BUDDY_MODEL=deepseek/deepseek-chat-v3.1
```

**Gemini direct:**

```env
GOOGLE_API_KEY=your_google_ai_api_key_here
STUDY_BUDDY_MODEL=gemini-2.5-flash
```

**Vertex AI:**

```env
GOOGLE_GENAI_USE_ENTERPRISE=true
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=asia-east2
STUDY_BUDDY_MODEL=gemini-2.5-flash
```

### Run

```powershell
.\.venv\Scripts\python.exe main.py
```

You should see something like:

```text
Study Buddy is ready.
LLM backend: OpenRouter (openrouter/deepseek/deepseek-chat-v3.1)
```

### Demo workflow

1. Place a PDF in `study_materials/` (for example `week_10_note.pdf`)
2. Start the app
3. Ask:

```text
Use week_10_note.pdf to generate revision points, key concepts, and study questions, then add them into my study plan.
```

4. Then ask:

```text
Read my saved study plan and turn it into a daily checklist with reminders.
```

5. Type `exit` to quit

### Offline PDF pipeline (no LLM)

Useful for testing PDF extraction without calling an API:

```powershell
.\.venv\Scripts\python.exe demo_pdf_pipeline.py
```

## Project Structure

```text
study-buddy-agent/
|-- main.py
|-- demo_pdf_pipeline.py
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
|-- study_plan.md
|-- study_materials/
|   |-- README.md
|   `-- .gitkeep
`-- study_buddy/
    |-- agents.py
    |-- config.py
    |-- mcp_integration.py
    |-- mcp_server.py
    `-- skills.py
```

## Architecture

### Agents

| Agent | Role |
|-------|------|
| Coordinator Agent | Routes student requests to the right specialist |
| Planner Agent | Builds deadline-aware study schedules |
| Research Agent | Generates revision notes from topics or PDFs |
| Reminder Agent | Turns plans into checklists and reminders |

### Agent skills

Python functions exposed as tools:

- `build_study_schedule()`
- `generate_revision_focus()`
- `extract_text_from_pdf_base64()`
- `merge_study_plan_with_notes()`
- `create_todo_reminders()`
- `analyze_student_request()`

### MCP server

`study_buddy/mcp_server.py` runs as a local subprocess and provides:

- `write_study_plan`
- `read_study_plan`
- `list_pdf_files`
- `extract_pdf_text`
- `get_pdf_file_info`
- `get_pdf_file_base64`


## Recommended OpenRouter models

| Use case | Model ID |
|----------|----------|
| General study assistant | `deepseek/deepseek-chat-v3.1` |
| Lower cost | `deepseek/deepseek-chat` |
| Faster responses | `deepseek/deepseek-v4-flash` |
| Harder PDF reasoning | `deepseek/deepseek-r1-0528` |

Browse more models at [openrouter.ai/models](https://openrouter.ai/models).

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No API key was provided` | Check `.env` exists and `load_dotenv()` runs before agents start |
| `429 RESOURCE_EXHAUSTED` on Gemini | Switch to OpenRouter or wait ~1 minute |
| Region blocked for Gemini | Use OpenRouter or Vertex AI |
| PDF not found | Put the file in `study_materials/` and use the exact filename |

## License

MIT License. See [LICENSE](LICENSE).

---

## 中文版本

### 專案簡介

`Study Buddy` 是一個用 Google ADK 建立的多代理學生溫習助手，幫學生把功課、deadline、lecture PDF 和溫習目標整理成可執行的溫習計劃、重點筆記和每日 to-do list。

### 功能

- 多 agent 分工：Coordinator、Planner、Research、Reminder
- 本地 MCP filesystem server，可讀寫 `study_plan.md`
- 從 `study_materials/` 抽取 PDF 文字
- 支援 Gemini、Vertex AI、OpenRouter（透過 LiteLLM）

### 安裝

```powershell
git clone https://github.com/YOUR_USERNAME/study-buddy-agent.git
cd study-buddy-agent
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
```

### 設定 `.env`

**OpenRouter（建議，適合香港 / 避開 Gemini 免費額度）：**

```env
STUDY_BUDDY_LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_API_BASE=https://openrouter.ai/api/v1
STUDY_BUDDY_MODEL=deepseek/deepseek-chat-v3.1
```

**直接使用 Gemini：**

```env
GOOGLE_API_KEY=your_google_ai_api_key_here
STUDY_BUDDY_MODEL=gemini-2.5-flash
```

### 執行

```powershell
.\.venv\Scripts\python.exe main.py
```

### 示範流程

1. 將 PDF 放入 `study_materials/`（例如 `week_10_note.pdf`）
2. 啟動程式
3. 輸入：

```text
Use week_10_note.pdf to generate revision points, key concepts, and study questions, then add them into my study plan.
```

4. 再輸入：

```text
Read my saved study plan and turn it into a daily checklist with reminders.
```

### 建議 OpenRouter 模型

| 用途 | 模型 |
|------|------|
| 一般溫習助手 | `deepseek/deepseek-chat-v3.1` |
| 更平 | `deepseek/deepseek-chat` |
| 更快 | `deepseek/deepseek-v4-flash` |
| 難 PDF 推理 | `deepseek/deepseek-r1-0528` |

### 常見問題

| 問題 | 解法 |
|------|------|
| `No API key was provided` | 檢查 `.env` 是否存在，以及設定是否正確 |
| Gemini `429` 額度不足 | 改用 OpenRouter 或等約 1 分鐘 |
| Gemini 地區被封 | 用 OpenRouter 或 Vertex AI |
| 搵唔到 PDF | 確認檔案已放入 `study_materials/` |
