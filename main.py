#!/usr/bin/env python3
"""
Whisper Summer School - Medical Transcription Pipeline
Whisper (STT) + BioMistral/OpenMed (SOAP Note Generator)
"""

import os
import sys
import argparse
from transcribe import transcribe_audio
from soap_generator import generate_soap_note, save_soap_note


def run_pipeline(audio_path: str, whisper_model: str = "base", llm_model: str = "biomistral"):
    """
    Pipeline lengkap: Audio → Transkrip → SOAP Note
    
    Args:
        audio_path: Path ke file audio
        whisper_model: tiny | base | small | medium | large
        llm_model: biomistral | medllama2
    """
    print("\n" + "="*55)
    print("  🏥 WHISPER SUMMER SCHOOL - MEDICAL PIPELINE")
    print("="*55)
    print(f"  📁 Audio     : {audio_path}")
    print(f"  🎙️  Whisper   : {whisper_model}")
    print(f"  🤖 LLM Model : {llm_model}")
    print("="*55 + "\n")

    # ── STEP 1: Transkripsi Audio ──────────────────────────
    print("📍 STEP 1: Transkripsi Audio dengan Whisper...")
    transcription = transcribe_audio(audio_path, model_size=whisper_model)
    
    transcript_text = transcription["text"]
    print(f"\n📝 Hasil Transkripsi ({len(transcript_text)} karakter):")
    print("-" * 40)
    print(transcript_text)
    print("-" * 40)

    # Simpan transkrip
    os.makedirs("outputs", exist_ok=True)
    transcript_file = "outputs/transcript_latest.txt"
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(transcript_text)
    print(f"💾 Transkrip disimpan: {transcript_file}")

    # ── STEP 2: Generate SOAP Note ─────────────────────────
    print("\n📍 STEP 2: Generate SOAP Note dengan BioMistral...")
    soap_note = generate_soap_note(transcript_text, model=llm_model)

    # ── STEP 3: Simpan Output ──────────────────────────────
    print("\n📍 STEP 3: Menyimpan Output...")
    output_file = save_soap_note(soap_note)

    print("\n" + "="*55)
    print("  ✅ PIPELINE SELESAI!")
    print(f"  📄 Output: {output_file}")
    print("="*55 + "\n")

    return {
        "transcript": transcript_text,
        "soap_note": soap_note,
        "output_file": output_file
    }


def main():
    parser = argparse.ArgumentParser(
        description="Medical Audio Transcription + SOAP Note Generator"
    )
    parser.add_argument(
        "audio", 
        help="Path ke file audio (mp3, wav, m4a, dll)"
    )
    parser.add_argument(
        "--whisper-model", 
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Ukuran model Whisper (default: base)"
    )
    parser.add_argument(
        "--llm-model",
        default="biomistral",
        choices=["biomistral", "medllama2"],
        help="Model LLM untuk SOAP note (default: biomistral)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.audio):
        print(f"❌ File tidak ditemukan: {args.audio}")
        sys.exit(1)

    result = run_pipeline(
        audio_path=args.audio,
        whisper_model=args.whisper_model,
        llm_model=args.llm_model
    )


if __name__ == "__main__":
    main()
