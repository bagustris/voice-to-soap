import whisper
import os
import sys

def transcribe_audio(audio_path: str, model_size: str = "base") -> dict:
    """
    Transkripsi file audio menggunakan OpenAI Whisper.
    
    Args:
        audio_path: Path ke file audio
        model_size: tiny | base | small | medium | large-v3-turbo
    
    Returns:
        dict dengan 'text' dan 'segments'
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"File audio tidak ditemukan: {audio_path}")

    print(f"🎙️  Loading Whisper model '{model_size}'...")
    model = whisper.load_model(model_size)

    print(f"🔊 Transkripsi: {audio_path}")
    result = model.transcribe(
        audio_path,
        language="id",        # Ganti "en" untuk English
        verbose=False
    )

    print("✅ Transkripsi selesai!")
    return {
        "text": result["text"].strip(),
        "segments": result.get("segments", []),
        "language": result.get("language", "unknown")
    }


# ── Jalankan langsung (tanpa import) ──────────────────────
if __name__ == "__main__":
    audio_file = sys.argv[1] if len(sys.argv) > 1 else "audio/sample_english.wav"
    
    if not os.path.exists(audio_file):
        print(f"❌ File tidak ditemukan: {audio_file}")
        print("Usage: python transcribe.py audio/namafile.mp3")
        sys.exit(1)

    result = transcribe_audio(audio_file)
    print("\n📝 Hasil Transkripsi:")
    print("-" * 40)
    print(result["text"])
    print("-" * 40)
    print(f"🌐 Bahasa terdeteksi: {result['language']}")
