"""
config.py — Konfigurasi terpusat untuk Whisper Summer School pipeline.

Ubah nilai BACKEND di sini, atau set environment variable:
    export OPENMED_BACKEND=ollama   # openmed | ollama | hf
"""

import os
from dataclasses import dataclass
from typing import Literal

# ─────────────────────────────────────────────
# AUTO-DETECT DEVICE (NVIDIA → MPS → CPU)
# ─────────────────────────────────────────────
def detect_device() -> str:
    """
    Deteksi hardware GPU secara otomatis:
      1. NVIDIA CUDA  → "cuda"
      2. Apple MLX    → "mps"
      3. Fallback     → "cpu"
    """
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🟢 GPU NVIDIA terdeteksi: {gpu_name} → device=cuda")
            return "cuda"
        if torch.backends.mps.is_available():
            print("🍎 Apple Silicon terdeteksi → device=mps")
            return "mps"
    except ImportError:
        pass  # torch belum terinstall, lanjut ke fallback

    print("🔵 Tidak ada GPU → device=cpu")
    return "cpu"


def detect_openmed_backend() -> str:
    """
    Untuk OpenMed, cek apakah openmed[mlx] tersedia (Apple Silicon).
    Jika tidak, gunakan backend HuggingFace biasa.
    Returns: "mlx" | "hf"
    """
    try:
        import mlx  # noqa: F401
        print("🍎 MLX tersedia → OpenMed akan pakai backend MLX")
        return "mlx"
    except ImportError:
        return "hf"


# Deteksi saat module di-load
AUTO_DEVICE: str = os.getenv("DEVICE", detect_device())
OPENMED_INFERENCE: str = detect_openmed_backend()


# ─────────────────────────────────────────────
# PILIH BACKEND SOAP
# ─────────────────────────────────────────────
BackendType = Literal["openmed", "ollama", "hf"]

# Local default: "ollama" (upstream default is "openmed")
BACKEND: BackendType = os.getenv("OPENMED_BACKEND", "ollama")


# ─────────────────────────────────────────────
# WHISPER CONFIG
# ─────────────────────────────────────────────
@dataclass
class WhisperConfig:
    model_size: str = os.getenv("WHISPER_MODEL", "base")
    # Options: tiny | base | small | medium | large-v3-turbo
    language: str = os.getenv("WHISPER_LANG", "auto")
    # "id" untuk Bahasa Indonesia, "en" untuk English, "auto" untuk deteksi otomatis
    fp16: bool = AUTO_DEVICE == "cuda"
    # fp16 otomatis aktif hanya di NVIDIA, nonaktif di MPS/CPU


# ─────────────────────────────────────────────
# OPENMED CONFIG
# ─────────────────────────────────────────────
@dataclass
class OpenMedConfig:
    ner_model: str = "openmed/medical-ner"
    # Referensi: https://openmed.life/docs/model-registry/

    deidentify_before_soap: bool = True
    deidentify_method: str = "replace"   # "mask" | "replace" | "redact"

    # Device otomatis dari hasil deteksi
    device: str = AUTO_DEVICE

    # Inference backend: "mlx" (Apple Silicon) | "hf" (lainnya)
    inference_backend: str = OPENMED_INFERENCE

    # REST service (opsional)
    service_host: str = os.getenv("OPENMED_HOST", "127.0.0.1")
    service_port: int = int(os.getenv("OPENMED_PORT", "8080"))


# ─────────────────────────────────────────────
# OLLAMA CONFIG
# ─────────────────────────────────────────────
@dataclass
class OllamaConfig:
    model: str = os.getenv("OLLAMA_MODEL", "llama3.2")
    temperature: float = 0.1
    num_predict: int = 1024
    host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")


# ─────────────────────────────────────────────
# HUGGINGFACE CONFIG
# ─────────────────────────────────────────────
@dataclass
class HuggingFaceConfig:
    model_name: str = "BioMistral/BioMistral-7B"
    max_new_tokens: int = 700
    temperature: float = 0.2
    # "cuda" | "mps" | "cpu" — ikut hasil deteksi otomatis
    device_map: str = AUTO_DEVICE


# ─────────────────────────────────────────────
# OUTPUT CONFIG
# ─────────────────────────────────────────────
@dataclass
class OutputConfig:
    output_dir: str = os.getenv("OUTPUT_DIR", "outputs")
    save_json: bool = True
    save_txt: bool = True
    save_transcript: bool = True


# ─────────────────────────────────────────────
# INSTANCE SIAP PAKAI
# ─────────────────────────────────────────────
whisper_cfg   = WhisperConfig()
openmed_cfg   = OpenMedConfig()
ollama_cfg    = OllamaConfig()
hf_cfg        = HuggingFaceConfig()
output_cfg    = OutputConfig()


# ─────────────────────────────────────────────
# HELPER: validasi backend
# ─────────────────────────────────────────────
def get_backend() -> BackendType:
    valid = ("openmed", "ollama", "hf")
    if BACKEND not in valid:
        raise ValueError(
            f"❌ Backend '{BACKEND}' tidak valid. "
            f"Pilih salah satu: {valid}\n"
            f"   Contoh: export OPENMED_BACKEND=ollama"
        )
    return BACKEND


def print_config() -> None:
    """Tampilkan konfigurasi aktif saat startup."""
    backend = get_backend()

    device_label = {
        "cuda": f"NVIDIA CUDA ({AUTO_DEVICE})",
        "mps":  "Apple Silicon (MPS/MLX)",
        "cpu":  "CPU only",
    }.get(AUTO_DEVICE, AUTO_DEVICE)

    print("=" * 48)
    print("  ⚙️  Whisper Summer School — Config")
    print("=" * 48)
    print(f"  Backend        : {backend.upper()}")
    print(f"  Device         : {device_label}")
    print(f"  Whisper model  : {whisper_cfg.model_size}")
    print(f"  Whisper fp16   : {whisper_cfg.fp16}")
    print(f"  Language       : {whisper_cfg.language}")
    print(f"  Output dir     : {output_cfg.output_dir}")
    print("-" * 48)

    if backend == "openmed":
        print(f"  OpenMed model  : {openmed_cfg.ner_model}")
        print(f"  Inference      : {openmed_cfg.inference_backend.upper()}")
        print(f"  PII de-id      : {openmed_cfg.deidentify_before_soap}")
        print(f"  De-id method   : {openmed_cfg.deidentify_method}")
    elif backend == "ollama":
        print(f"  Ollama model   : {ollama_cfg.model}")
        print(f"  Ollama host    : {ollama_cfg.host}")
        print(f"  Temperature    : {ollama_cfg.temperature}")
    elif backend == "hf":
        print(f"  HF model       : {hf_cfg.model_name}")
        print(f"  Device map     : {hf_cfg.device_map}")
    print("=" * 48)


# ─────────────────────────────────────────────
# Jalankan langsung untuk cek konfigurasi
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print_config()
