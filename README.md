# 🏥 Whisper Summer School — Medical Transcription Pipeline

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Gradio](https://img.shields.io/badge/Gradio-6.0+-orange.svg)](https://gradio.app)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)]()

**[🇮🇩 Bahasa Indonesia](#-bahasa-indonesia) · [🇬🇧 English](#-english)**

</div>

---

# 🇮🇩 Bahasa Indonesia

Pipeline AI untuk **transkripsi audio medis otomatis** dan pembuatan **catatan SOAP** menggunakan OpenAI Whisper + LLM medis lokal.

> ⚠️ **Disclaimer:** Output AI bersifat *advisory* dan wajib ditinjau oleh tenaga medis profesional sebelum digunakan secara klinis.

## ✨ Fitur Utama

- 🎙️ **Transkripsi otomatis** percakapan dokter-pasien via OpenAI Whisper
- 📋 **Generasi SOAP note** terstruktur (Subjective / Objective / Assessment / Plan)
- 🔒 **PII De-identification** — nama & data sensitif otomatis di-mask (via OpenMed)
- 🍎 **Apple Silicon optimized** — auto-detect MPS/MLX
- ⚡ **Multi-backend LLM** — OpenMed, Ollama, atau HuggingFace
- 🖥️ **Gradio UI** — antarmuka web dengan mikrofon, SOAP viewer & download

---

## 🗂️ Struktur Project

```
whisper-summer-school/
├── main.py                  # Pipeline utama (CLI)
├── config.py                # Konfigurasi terpusat (device, model, backend)
├── transcribe.py            # Modul transkripsi Whisper
├── soap_generator.py        # SOAP via Ollama (medllama2, mistral, dll)
├── soap_openmed.py          # SOAP via OpenMed (NER + PII de-id)
├── app.py                   # Gradio UI — transkripsi sederhana
├── app_emr_demo.py          # Gradio UI — demo EMR lengkap
├── requirements.txt         # Dependensi Python
├── legacy/
│   └── soap_from_transcript.py  # HuggingFace backend (arsip)
├── audio/                   # File audio input (tidak di-commit)
└── outputs/                 # Hasil transkrip & SOAP (tidak di-commit)
```

---

## ⚙️ Instalasi

### 1. Clone & buat virtual environment

```bash
git clone https://github.com/<username>/whisper-summer-school.git
cd whisper-summer-school

python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 2. Install dependensi

```bash
pip install -r requirements.txt
```

### 3. Install backend LLM (pilih salah satu)

#### 🥇 OpenMed — Direkomendasikan

```bash
pip install "openmed[mlx]"   # Apple Silicon (M1/M2/M3/M4)
pip install openmed           # CPU atau NVIDIA
```

#### 🦙 Ollama — Lokal, mudah digunakan

```bash
# Install Ollama: https://ollama.com
ollama pull medllama2       # Model medis (3.8 GB)
ollama pull mistral         # General purpose (4 GB)
ollama pull llama3.2        # Ringan & cepat (2 GB)

ollama serve                # Jalankan server (terminal terpisah)
```

---

## 🚀 Cara Penggunaan

### CLI

```bash
python main.py audio/sample.mp3                              # Default (OpenMed)
python main.py audio/sample.mp3 --backend ollama --model medllama2
python main.py audio/sample.mp3 --no-soap                   # Transkripsi saja
python main.py audio/sample.mp3 --whisper-model small --lang en
```

### Semua Flag CLI

| Flag | Shorthand | Default | Keterangan |
|------|-----------|---------|------------|
| `--backend` | `-b` | `openmed` | `openmed` / `ollama` / `hf` |
| `--model` | `-m` | `medllama2` | Nama model Ollama |
| `--whisper-model` | `-w` | `base` | Ukuran model Whisper |
| `--lang` | `-l` | `id` | `id` / `en` / `auto` |
| `--no-soap` | — | `False` | Skip generasi SOAP |

### Gradio Web UI

```bash
python app_emr_demo.py
```

> 🎙️ **Mikrofon:** Selalu buka via **`http://localhost:PORT`** — bukan `http://0.0.0.0:PORT`
> Browser hanya mengizinkan akses mikrofon di [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts),
> dan `localhost` dianggap secure meskipun tanpa HTTPS.

#### Fitur Web UI

| Fitur | Keterangan |
|-------|-----------|
| 🎙️ Upload / Rekam | Upload file audio atau rekam via mikrofon |
| 🤖 Pilih Backend | `openmed` / `ollama` / `hf` |
| 🦙 Pilih Model Ollama | Dropdown dinamis dari `ollama list` |
| 🎙️ Pilih Whisper Model | `tiny` → `large-v3-turbo` |
| 🌐 Pilih Bahasa | `id` / `en` / `auto` |
| 🔒 De-identifikasi PII | Mask nama & data sensitif |
| 📝 Transkrip Viewer | Tampil di tab Transkrip |
| 📋 SOAP Viewer | Tampil di tab SOAP Note |
| 🗂️ JSON Viewer | Tampil di tab JSON |
| ⬇️ Download | `transcript.txt` · `soap.txt` · `soap.json` |

---

## 🤖 Perbandingan Backend LLM

| Backend | Keunggulan | Kelemahan | Kebutuhan |
|---------|-----------|-----------|-----------|
| **OpenMed** | PII de-id, 1000+ model medis, MLX native | Perlu install extra | `pip install "openmed[mlx]"` |
| **Ollama** | Mudah, model bisa diganti, stabil | Perlu `ollama serve` | `ollama pull medllama2` |
| **HuggingFace** | Tanpa server tambahan | Butuh VRAM besar (14GB+) | GPU recommended |

---

## 🎙️ Model Whisper

| Model | VRAM | Kecepatan | Akurasi | Rekomendasi |
|-------|------|-----------|---------|-------------|
| `tiny` | ~1 GB | ⚡⚡⚡⚡ | ⭐⭐ | Testing cepat |
| `base` | ~1 GB | ⚡⚡⚡ | ⭐⭐⭐ | **Default** |
| `small` | ~2 GB | ⚡⚡ | ⭐⭐⭐⭐ | Recommended |
| `medium` | ~5 GB | ⚡ | ⭐⭐⭐⭐⭐ | Akurasi tinggi |
| `large-v3-turbo` | ~6 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Best quality |

---

## 📋 Format Output SOAP

```
=======================================================
         CATATAN MEDIS — FORMAT SOAP
  Dibuat : 2026-06-30T01:25:00
  Model  : medllama2:latest
=======================================================

[S — Subjective (Keluhan Pasien)]
• Dizziness selama beberapa bulan
• Hearing loss dan tinnitus (ringing in ears)

[O — Objective (Temuan Klinis)]
• Pasien tampak comfortable
• Blood pressure 120/80, HR 72

[A — Assessment (Penilaian)]
• Consistent with Meniere's disease

[P — Plan (Rencana Tindakan)]
• Prescribe betahistine 16mg twice daily
• Referral to audiology
• Follow-up in 4 weeks
=======================================================
```

Output disimpan otomatis ke `outputs/`:
- `transcript_<nama>_<timestamp>.txt`
- `soap_<nama>_<timestamp>.txt`
- `soap_<nama>_<timestamp>.json`

---

## 🛠️ Konfigurasi (`config.py`)

```python
BACKEND = "openmed"              # "openmed" | "ollama" | "hf"
whisper_cfg.model_size = "base"  # tiny/base/small/medium/large-v3-turbo
whisper_cfg.language   = "id"    # "id" | "en" | "auto"
ollama_cfg.model       = "medllama2"
openmed_cfg.deidentify_before_soap = True
```

---

## 🔒 Privasi & Keamanan

- ✅ **100% lokal** — tidak ada data dikirim ke server eksternal
- ✅ **PII De-identification** — nama pasien & data sensitif otomatis di-mask
- ✅ **HIPAA-aware** — OpenMed mendukung 247 checkpoint de-identifikasi
- ❌ **Jangan commit** data pasien ke repository publik

---

## 🐛 Troubleshooting

| Masalah | Solusi |
|---------|--------|
| `FP16 not supported on CPU` | Sudah di-suppress otomatis |
| Mikrofon tidak aktif | Buka via `http://localhost:PORT`, bukan `http://0.0.0.0:PORT` |
| `ollama: model not found` | Jalankan `ollama pull medllama2` |
| NumPy / Numba conflict | `pip install "numpy==1.26.4"` |
| MPS out of memory | Gunakan `--whisper-model tiny` |

---

## 🗺️ Roadmap

- [x] Transkripsi Whisper multi-device (CPU / MPS / CUDA)
- [x] SOAP generation via Ollama
- [x] SOAP generation via OpenMed (NER + PII de-id)
- [x] Auto-detect Apple Silicon / NVIDIA / CPU
- [x] Multi-layer response parser (JSON → header → regex → fallback)
- [x] Gradio UI — transkripsi sederhana (`app.py`)
- [x] Gradio UI — EMR demo lengkap (`app_emr_demo.py`)
- [x] SOAP viewer & download (txt + json) di Web UI
- [x] Mikrofon aktif di localhost (secure context fix)
- [ ] Whisper `large-v3-turbo` benchmark di Apple Silicon
- [ ] Output PDF dari SOAP note
- [ ] Batch processing multiple audio files

---

## 👥 Kontribusi

Pull request dan issue sangat disambut! Pastikan:
1. Tidak menyertakan data pasien nyata
2. Test pipeline: `python main.py audio/sample.mp3 --no-soap`
3. Update README jika menambah fitur baru

---

## 📄 Lisensi

MIT License — bebas digunakan untuk keperluan edukasi dan riset.

---
---

# 🇬🇧 English

An AI pipeline for **automated medical audio transcription** and **SOAP note generation** using OpenAI Whisper + local medical LLMs.

> ⚠️ **Disclaimer:** AI output is *advisory* only and must be reviewed by a qualified medical professional before any clinical use.

## ✨ Key Features

- 🎙️ **Automatic transcription** of doctor-patient conversations via OpenAI Whisper
- 📋 **Structured SOAP note generation** (Subjective / Objective / Assessment / Plan)
- 🔒 **PII De-identification** — names & sensitive data auto-masked (via OpenMed)
- 🍎 **Apple Silicon optimized** — auto-detect MPS/MLX
- ⚡ **Multi-backend LLM** — OpenMed, Ollama, or HuggingFace
- 🖥️ **Gradio UI** — web interface with microphone, SOAP viewer & file downloads

---

## 🗂️ Project Structure

```
whisper-summer-school/
├── main.py                  # Main pipeline (CLI)
├── config.py                # Centralized config (device, model, backend)
├── transcribe.py            # Whisper transcription module
├── soap_generator.py        # SOAP via Ollama (medllama2, mistral, etc.)
├── soap_openmed.py          # SOAP via OpenMed (NER + PII de-id)
├── app.py                   # Gradio UI — simple transcription
├── app_emr_demo.py          # Gradio UI — full EMR demo
├── requirements.txt         # Python dependencies
├── legacy/
│   └── soap_from_transcript.py  # HuggingFace backend (archived)
├── audio/                   # Audio input files (not committed)
└── outputs/                 # Transcripts & SOAP results (not committed)
```

---

## ⚙️ Installation

### 1. Clone & create virtual environment

```bash
git clone https://github.com/<username>/whisper-summer-school.git
cd whisper-summer-school

python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Install LLM backend (choose one)

#### 🥇 OpenMed — Recommended

```bash
pip install "openmed[mlx]"   # Apple Silicon (M1/M2/M3/M4)
pip install openmed           # CPU or NVIDIA
```

#### 🦙 Ollama — Easy local inference

```bash
# Install Ollama: https://ollama.com
ollama pull medllama2       # Medical model (3.8 GB)
ollama pull mistral         # General purpose (4 GB)
ollama pull llama3.2        # Lightweight & fast (2 GB)

ollama serve                # Start server (separate terminal)
```

---

## 🚀 Usage

### CLI

```bash
python main.py audio/sample.mp3                              # Default (OpenMed)
python main.py audio/sample.mp3 --backend ollama --model medllama2
python main.py audio/sample.mp3 --no-soap                   # Transcription only
python main.py audio/sample.mp3 --whisper-model small --lang en
```

### All CLI Flags

| Flag | Shorthand | Default | Description |
|------|-----------|---------|-------------|
| `--backend` | `-b` | `openmed` | `openmed` / `ollama` / `hf` |
| `--model` | `-m` | `medllama2` | Ollama model name |
| `--whisper-model` | `-w` | `base` | Whisper model size |
| `--lang` | `-l` | `id` | `id` / `en` / `auto` |
| `--no-soap` | — | `False` | Skip SOAP generation |

### Gradio Web UI

```bash
python app_emr_demo.py
```

> 🎙️ **Microphone:** Always open via **`http://localhost:PORT`** — NOT `http://0.0.0.0:PORT`
> Browsers only allow microphone access in a [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts),
> and `localhost` is treated as secure even without HTTPS.

#### Web UI Features

| Feature | Description |
|---------|-------------|
| 🎙️ Upload / Record | Upload audio file or record via microphone |
| 🤖 Backend selector | `openmed` / `ollama` / `hf` |
| 🦙 Ollama model | Dynamic dropdown from `ollama list` |
| 🎙️ Whisper model | `tiny` → `large-v3-turbo` |
| 🌐 Language | `id` / `en` / `auto` |
| 🔒 PII De-identification | Mask names & sensitive data before processing |
| 📝 Transcript Viewer | Displayed in Transcript tab |
| 📋 SOAP Viewer | Displayed in SOAP Note tab |
| 🗂️ JSON Viewer | Displayed in JSON tab |
| ⬇️ Download | `transcript.txt` · `soap.txt` · `soap.json` |

---

## 🤖 LLM Backend Comparison

| Backend | Strengths | Weaknesses | Requirements |
|---------|-----------|------------|--------------|
| **OpenMed** | PII de-id, 1000+ medical models, MLX native | Extra install needed | `pip install "openmed[mlx]"` |
| **Ollama** | Easy, swappable models, stable | Requires `ollama serve` | `ollama pull medllama2` |
| **HuggingFace** | No extra server | Needs large VRAM (14GB+) | GPU recommended |

---

## 🎙️ Whisper Models

| Model | VRAM | Speed | Accuracy | Recommendation |
|-------|------|-------|----------|----------------|
| `tiny` | ~1 GB | ⚡⚡⚡⚡ | ⭐⭐ | Quick testing |
| `base` | ~1 GB | ⚡⚡⚡ | ⭐⭐⭐ | **Default** |
| `small` | ~2 GB | ⚡⚡ | ⭐⭐⭐⭐ | Recommended |
| `medium` | ~5 GB | ⚡ | ⭐⭐⭐⭐⭐ | High accuracy |
| `large-v3-turbo` | ~6 GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | Best quality |

---

## 📋 SOAP Output Format

```
=======================================================
         MEDICAL RECORD — SOAP FORMAT
  Generated : 2026-06-30T01:25:00
  Model     : medllama2:latest
=======================================================

[S — Subjective (Patient Complaints)]
• Dizziness for several months
• Hearing loss and tinnitus (ringing in ears)

[O — Objective (Clinical Findings)]
• Patient appears comfortable
• Blood pressure 120/80, HR 72

[A — Assessment]
• Consistent with Meniere's disease

[P — Plan]
• Prescribe betahistine 16mg twice daily
• Referral to audiology
• Follow-up in 4 weeks
=======================================================
```

Output saved automatically to `outputs/`:
- `transcript_<name>_<timestamp>.txt`
- `soap_<name>_<timestamp>.txt`
- `soap_<name>_<timestamp>.json`

---

## 🛠️ Configuration (`config.py`)

```python
BACKEND = "openmed"              # "openmed" | "ollama" | "hf"
whisper_cfg.model_size = "base"  # tiny/base/small/medium/large-v3-turbo
whisper_cfg.language   = "id"    # "id" | "en" | "auto"
ollama_cfg.model       = "medllama2"
openmed_cfg.deidentify_before_soap = True
```

---

## 🔒 Privacy & Security

- ✅ **100% local** — no data sent to external servers
- ✅ **PII De-identification** — patient names & sensitive data auto-masked
- ✅ **HIPAA-aware** — OpenMed supports 247 de-identification checkpoints
- ❌ **Never commit** real patient data to a public repository

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| `FP16 not supported on CPU` | Auto-suppressed, no action needed |
| Microphone not working | Open via `http://localhost:PORT`, NOT `http://0.0.0.0:PORT` |
| `ollama: model not found` | Run `ollama pull medllama2` |
| NumPy / Numba conflict | `pip install "numpy==1.26.4"` |
| MPS out of memory | Use `--whisper-model tiny` |

---

## 🗺️ Roadmap

- [x] Whisper transcription multi-device (CPU / MPS / CUDA)
- [x] SOAP generation via Ollama
- [x] SOAP generation via OpenMed (NER + PII de-id)
- [x] Auto-detect Apple Silicon / NVIDIA / CPU
- [x] Multi-layer response parser (JSON → header → regex → fallback)
- [x] Gradio UI — simple transcription (`app.py`)
- [x] Gradio UI — full EMR demo (`app_emr_demo.py`)
- [x] SOAP viewer & download (txt + json) in Web UI
- [x] Microphone fix for localhost (secure context)
- [ ] Whisper `large-v3-turbo` benchmark on Apple Silicon
- [ ] PDF export from SOAP note
- [ ] Batch processing multiple audio files

---

## 👥 Contributing

Pull requests and issues are welcome! Please ensure:
1. No real patient data is included
2. Test the pipeline before PR: `python main.py audio/sample.mp3 --no-soap`
3. Update README if adding new features

---

## 📄 License

MIT License — free to use for educational and research purposes.
