# 🏥 Whisper Summer School

A medical audio transcription and SOAP note generation project built for educational purposes.  
Uses **OpenAI Whisper** for speech-to-text and **BioMistral** for clinical documentation.

> ⚠️ **For educational use only.** All generated SOAP notes require clinician review before any clinical use.

---

## 📁 Project Structure

```
whisper-summer-school/
├── app.py                  # Gradio UI: Whisper STT only (simple demo)
├── app_emr_demo.py         # Gradio UI: Whisper + rule-based SOAP (no LLM)
├── main.py                 # CLI: Full pipeline (Whisper + BioMistral via Ollama)
├── transcribe.py           # Module: Audio transcription with Whisper
├── soap_generator.py       # Module: SOAP generation via BioMistral (Ollama)
├── soap_from_transcript.py # Module: SOAP generation via BioMistral (HuggingFace)
├── requirements.txt        # Python dependencies
├── audio/                  # 🔒 Audio input files (gitignored)
└── outputs/                # 🔒 Transcripts & SOAP notes (gitignored)
```

---

## 🧩 How Each File Works

### `app.py` — Simple STT Demo
- Gradio web interface
- Upload or record audio → get transcript
- Uses Whisper `base` model
- **Run:** `python app.py`

### `app_emr_demo.py` — EMR Demo (No LLM Required)
- Gradio web interface
- Upload audio → transcript + rule-based SOAP draft
- Does **not** require Ollama or GPU
- Best for quick demos without LLM setup
- **Run:** `python app_emr_demo.py`

### `main.py` — Full CLI Pipeline
- Command-line interface
- Full pipeline: Audio → Whisper → BioMistral → SOAP note saved to `outputs/`
- Requires Ollama running locally
- **Run:** `python main.py audio/sample.mp3`

### `transcribe.py` — Whisper Module
- Reusable transcription module
- Imported by `main.py`
- Can also run standalone
- **Run:** `python transcribe.py audio/sample.mp3`

### `soap_generator.py` — SOAP via Ollama
- Uses BioMistral locally via Ollama
- Returns structured JSON SOAP note
- Saves `.json` and `.txt` to `outputs/`
- Requires: `ollama pull biomistral`
- **Run:** `python soap_generator.py`

### `soap_from_transcript.py` — SOAP via HuggingFace
- Uses BioMistral directly via `transformers`
- Alternative to Ollama approach
- Downloads model from HuggingFace (~14GB)
- **Run:** `python soap_from_transcript.py`

---

## ⚙️ Installation

### 1. Clone the repository
```bash
git clone git@github.com:oskarriandi/whisper-summer-school.git
cd whisper-summer-school
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install Ollama (for full LLM pipeline)
```bash
# macOS
brew install ollama

# Pull BioMistral model (~4.5GB)
ollama pull biomistral
```

### 5. Install FFmpeg (required by Whisper)
```bash
brew install ffmpeg
```

---

## 🚀 Usage

### Option A — Simple Demo (No LLM)
```bash
python app.py
# Open http://localhost:7860
```

### Option B — EMR Demo with SOAP (No LLM)
```bash
python app_emr_demo.py
# Open http://localhost:7860
```

### Option C — Full Pipeline via CLI (With LLM)
```bash
# Start Ollama first
ollama serve

# Run pipeline
python main.py audio/your_audio.mp3

# With options
python main.py audio/your_audio.mp3 --whisper-model small --llm-model biomistral
```

### Option D — Run modules individually
```bash
# Transcription only
python transcribe.py audio/your_audio.mp3

# SOAP generation only (from text)
python soap_generator.py

# SOAP via HuggingFace (downloads model automatically)
python soap_from_transcript.py
```

---

## 🤖 Models Used

| Component | Model | Size | Backend |
|-----------|-------|------|---------|
| Speech-to-Text | OpenAI Whisper `base` | ~150MB | Local |
| SOAP Generation | BioMistral-7B Q4 | ~4.5GB | Ollama |
| SOAP (alternative) | BioMistral-7B fp16 | ~14GB | HuggingFace |

### Whisper Model Options
| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | 75MB | ⚡⚡⚡⚡ | ⭐⭐ |
| `base` | 150MB | ⚡⚡⚡ | ⭐⭐⭐ |
| `small` | 500MB | ⚡⚡ | ⭐⭐⭐⭐ |
| `medium` | 1.5GB | ⚡ | ⭐⭐⭐⭐⭐ |

---

## 📋 Requirements

- Python 3.11+
- macOS / Linux
- FFmpeg
- Ollama (optional, for full LLM pipeline)
- GPU recommended for `soap_from_transcript.py`

---

## 🔒 Privacy & Security

- `audio/` and `outputs/` are **gitignored** — never committed to GitHub
- All processing runs **100% locally** — no data sent to external servers
- Generated SOAP notes are drafts only — **always require clinician review**

---

## 📚 References

- [OpenAI Whisper](https://github.com/openai/whisper)
- [BioMistral on HuggingFace](https://huggingface.co/BioMistral/BioMistral-7B)
- [Ollama](https://ollama.com)
- [Gradio](https://gradio.app)
