# 🏥 Whisper Summer School — Medical Transcription Pipeline

Pipeline AI untuk **transkripsi audio medis otomatis** dan pembuatan **catatan SOAP** menggunakan OpenAI Whisper + LLM medis lokal.

> ⚠️ **Disclaimer:** Output AI bersifat *advisory* dan wajib ditinjau oleh tenaga medis profesional sebelum digunakan secara klinis.

---

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

#### 🥇 OpenMed — Recommended (Apple Silicon / CPU / NVIDIA)

```bash
# Apple Silicon (M1/M2/M3/M4)
pip install "openmed[mlx]"

# CPU atau NVIDIA
pip install openmed
```

#### 🦙 Ollama — Lokal, mudah digunakan

```bash
# Install Ollama: https://ollama.com
ollama pull medllama2       # Model medis (3.8 GB)
ollama pull mistral         # General purpose (4 GB)
ollama pull llama3.2        # Ringan & cepat (2 GB)

# Jalankan server Ollama (terminal terpisah)
ollama serve
```

---

## 🚀 Cara Penggunaan

### CLI — Pipeline Lengkap

```bash
# Default (OpenMed backend)
python main.py audio/sample.mp3

# Pakai Ollama + medllama2
python main.py audio/sample.mp3 --backend ollama --model medllama2

# Pakai Ollama + model lain
python main.py audio/sample.mp3 --backend ollama --model mistral

# Hanya transkripsi, skip SOAP
python main.py audio/sample.mp3 --no-soap

# Override model Whisper & bahasa
python main.py audio/sample.mp3 --whisper-model small --lang en
```

### Semua Flag CLI

| Flag | Shorthand | Default | Keterangan |
|------|-----------|---------|------------|
| `--backend` | `-b` | `openmed` | Backend LLM: `openmed` / `ollama` / `hf` |
| `--model` | `-m` | `medllama2` | Nama model Ollama (hanya untuk `--backend ollama`) |
| `--whisper-model` | `-w` | `base` | Ukuran model Whisper |
| `--lang` | `-l` | `id` | Bahasa: `id`, `en`, `auto` |
| `--no-soap` | — | `False` | Skip generasi SOAP |

### Gradio UI

```bash
# UI transkripsi sederhana
python app.py

# UI demo EMR lengkap (Whisper + SOAP + Download)
python app_emr_demo.py
```

> 🎙️ **Mikrofon:** Selalu buka via **`http://localhost:PORT`** — bukan `http://0.0.0.0:PORT`
> Browser hanya mengizinkan akses mikrofon di [secure context](https://developer.mozilla.org/en-US/docs/Web/Security/Secure_Contexts),
> dan `localhost` dianggap secure meskipun tanpa HTTPS.

#### Fitur Web UI (`app_emr_demo.py`)

| Fitur | Keterangan |
|-------|-----------|
| 🎙️ Upload / Rekam | Upload file audio atau rekam langsung via mikrofon |
| 🤖 Pilih Backend | `openmed` / `ollama` / `hf` |
| 🦙 Pilih Model Ollama | Dropdown dinamis dari `ollama list` |
| 🎙️ Pilih Whisper Model | `tiny` → `large-v3-turbo` |
| 🌐 Pilih Bahasa | `id` / `en` / `auto` |
| 🔒 De-identifikasi PII | Mask nama & data sensitif sebelum diproses |
| 📝 Transkrip Viewer | Tampil langsung di tab Transkrip |
| 📋 SOAP Viewer | Tampil langsung di tab SOAP Note |
| 🗂️ JSON Viewer | Tampil langsung di tab JSON |
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

```bash
# Ganti model Whisper di config.py atau via flag:
python main.py audio/sample.mp3 --whisper-model small
```

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
  ⚠️  DISCLAIMER: Output ini bersifat advisory.
  Tidak untuk digunakan sebagai keputusan klinis.
=======================================================
```

Output disimpan otomatis ke folder `outputs/`:
- `transcript_<nama>_<timestamp>.txt`
- `soap_<nama>_<timestamp>.txt`
- `soap_<nama>_<timestamp>.json`

---

## 🛠️ Konfigurasi (`config.py`)

Semua pengaturan default ada di `config.py`:

```python
# Backend LLM default
BACKEND = "openmed"          # "openmed" | "ollama" | "hf"

# Whisper
whisper_cfg.model_size = "base"
whisper_cfg.language   = "id"   # "id" | "en" | "auto"

# Ollama
ollama_cfg.model       = "medllama2"
ollama_cfg.temperature = 0.3

# OpenMed
openmed_cfg.deidentify_before_soap = True
openmed_cfg.deidentify_method      = "mask"
```

---

## 🔒 Privasi & Keamanan

- ✅ **100% lokal** — tidak ada data yang dikirim ke server eksternal
- ✅ **PII De-identification** — nama pasien & data sensitif otomatis di-mask
- ✅ **HIPAA-aware** — OpenMed mendukung 247 checkpoint de-identifikasi
- ❌ **Jangan commit** data pasien ke repository publik (sudah ada di `.gitignore`)

---

## 🐛 Troubleshooting

### Whisper: `FP16 is not supported on CPU`
```
# Sudah di-suppress otomatis. Tidak perlu tindakan.
```

### Mikrofon tidak aktif di browser
```
# Pastikan buka via http://localhost:PORT
# BUKAN http://0.0.0.0:PORT — browser blokir mic di non-secure context
```

### Ollama: `model not found`
```bash
ollama list                    # cek model yang tersedia
ollama pull medllama2          # download model
ollama serve                   # pastikan server berjalan
```

### NumPy / Numba conflict
```bash
pip install "numpy==1.26.4"
```

### OpenMed tidak terinstall
```bash
pip install "openmed[mlx]"     # Apple Silicon
pip install openmed            # CPU / NVIDIA
```

### MPS out of memory (Apple Silicon)
```bash
# Gunakan model Whisper yang lebih kecil
python main.py audio/sample.mp3 --whisper-model tiny
```

---

## 📦 Requirements

```
openai-whisper
torch
ollama
gradio>=6.0
numpy==1.26.4
openmed[mlx]    # opsional, Apple Silicon
openmed         # opsional, CPU/NVIDIA
```

Install semua:
```bash
pip install -r requirements.txt
```

---

## 🗺️ Roadmap

- [x] Transkripsi Whisper multi-device (CPU / MPS / CUDA)
- [x] SOAP generation via Ollama (medllama2, mistral, dll)
- [x] SOAP generation via OpenMed (NER + PII de-id)
- [x] Auto-detect Apple Silicon / NVIDIA / CPU
- [x] Multi-layer response parser (JSON → header → regex → fallback)
- [x] Gradio UI — transkripsi sederhana (`app.py`)
- [x] Gradio UI — EMR demo lengkap (`app_emr_demo.py`)
- [x] SOAP viewer & download (txt + json) di Web UI
- [x] Mikrofon aktif di localhost (secure context fix)
- [ ] Install & test `openmed[mlx]` end-to-end
- [ ] Whisper `large-v3-turbo` benchmark di Apple Silicon
- [ ] Output PDF dari SOAP note
- [ ] Batch processing multiple audio files

---

## 👥 Kontribusi

Pull request dan issue sangat disambut! Pastikan:
1. Tidak menyertakan data pasien nyata
2. Test pipeline sebelum PR: `python main.py audio/sample.mp3 --no-soap`
3. Update README jika menambah fitur baru

---

## 📄 Lisensi

MIT License — bebas digunakan untuk keperluan edukasi dan riset.
