"""
app_emr_demo.py — Gradio UI untuk demo EMR lengkap.
Compatible: Gradio 6.0+

Microphone fix:
  - server_name="127.0.0.1" agar browser anggap sebagai secure context
  - Buka di http://localhost:PORT (bukan http://0.0.0.0:PORT)
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import gradio as gr

from config import (
    BACKEND, AUTO_DEVICE,
    whisper_cfg, ollama_cfg, openmed_cfg, output_cfg,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _get_ollama_models() -> list[str]:
    try:
        import ollama
        models = [m.model for m in ollama.list().models]
        return models if models else ["medllama2:latest"]
    except Exception:
        return ["medllama2:latest"]


def _device_label() -> str:
    labels = {
        "cuda": "⚡ NVIDIA CUDA",
        "mps":  "🍎 Apple Silicon (MPS)",
        "cpu":  "🔵 CPU",
    }
    return labels.get(AUTO_DEVICE, AUTO_DEVICE)


# ─────────────────────────────────────────────────────────────────────────────
# CORE PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    audio_path: str,
    backend: str,
    ollama_model: str,
    whisper_model_size: str,
    language: str,
    skip_soap: bool,
    deidentify: bool,
) -> tuple[str, str, str, str, str, str, str]:
    """
    Returns:
        (log, transcript, soap_text, soap_json,
         dl_transcript, dl_soap_txt, dl_soap_json)
    """
    logs       = []
    transcript = ""
    soap_text  = ""
    soap_json  = ""

    def log(msg: str):
        logs.append(msg)

    # ── Validasi ──────────────────────────────────────────────────────────────
    if audio_path is None:
        return "❌ Tidak ada file audio.", "", "", "", None, None, None

    # ── STEP 1: Transkripsi ───────────────────────────────────────────────────
    log("📍 STEP 1: Transkripsi Whisper...")
    log(f"   Model  : {whisper_model_size}")
    log(f"   Bahasa : {language}")
    log(f"   Device : {_device_label()}")

    try:
        import whisper
        device = "cuda" if AUTO_DEVICE == "cuda" else "cpu"
        fp16   = device == "cuda"

        log(f"   ⏳ Loading model '{whisper_model_size}'...")
        model  = whisper.load_model(whisper_model_size, device=device)
        log("   🔊 Memproses audio...")
        result = model.transcribe(
            audio_path,
            language=language if language != "auto" else None,
            fp16=fp16,
            verbose=False,
        )
        transcript = result["text"].strip()
        log(f"   ✅ Selesai! ({len(transcript)} karakter)\n")

    except Exception as e:
        log(f"   ❌ Transkripsi gagal: {e}")
        return "\n".join(logs), "", "", "", None, None, None

    # ── STEP 2: Generate SOAP ─────────────────────────────────────────────────
    soap_result = None

    if skip_soap:
        log("⏭️  STEP 2: SOAP dilewati.")
    else:
        log(f"📍 STEP 2: Generate SOAP [{backend.upper()}]...")
        openmed_cfg.deidentify_before_soap = deidentify

        try:
            if backend == "openmed":
                from soap_openmed import generate_soap
                soap_result = generate_soap(transcript)

            elif backend == "ollama":
                from soap_generator import generate_soap_note
                soap_result = generate_soap_note(transcript, model=ollama_model)

            elif backend == "hf":
                try:
                    from legacy.soap_from_transcript import generate_soap_hf
                except ImportError:
                    from soap_from_transcript import generate_soap_hf
                soap_result = generate_soap_hf(transcript)

            log("   ✅ SOAP berhasil dibuat!\n")

        except Exception as e:
            log(f"   ⚠️  SOAP gagal: {e}")

    # ── Format SOAP output ────────────────────────────────────────────────────
    if soap_result is not None:
        if hasattr(soap_result, "to_text"):
            soap_text = soap_result.to_text()
            soap_json = json.dumps(soap_result.to_dict(), ensure_ascii=False, indent=2)
        elif isinstance(soap_result, str):
            soap_text = soap_result
            soap_json = json.dumps({"raw": soap_result}, ensure_ascii=False, indent=2)
        elif isinstance(soap_result, dict):
            soap_text = "\n".join(f"[{k}]\n{v}" for k, v in soap_result.items())
            soap_json = json.dumps(soap_result, ensure_ascii=False, indent=2)

    # ── STEP 3: Simpan file ───────────────────────────────────────────────────
    log("📍 STEP 3: Menyimpan output...")
    os.makedirs(output_cfg.output_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    dl_transcript = os.path.join(output_cfg.output_dir, f"transcript_{ts}.txt")
    with open(dl_transcript, "w", encoding="utf-8") as f:
        f.write(transcript)
    log(f"   💾 {dl_transcript}")

    dl_soap_txt = None
    if soap_text:
        dl_soap_txt = os.path.join(output_cfg.output_dir, f"soap_{ts}.txt")
        with open(dl_soap_txt, "w", encoding="utf-8") as f:
            f.write(soap_text)
        log(f"   💾 {dl_soap_txt}")

    dl_soap_json = None
    if soap_json:
        dl_soap_json = os.path.join(output_cfg.output_dir, f"soap_{ts}.json")
        with open(dl_soap_json, "w", encoding="utf-8") as f:
            f.write(soap_json)
        log(f"   💾 {dl_soap_json}")

    log("\n✅ Pipeline selesai!")
    return (
        "\n".join(logs),
        transcript,
        soap_text,
        soap_json,
        dl_transcript,
        dl_soap_txt,
        dl_soap_json,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────

_CSS = """
  .header-box { text-align: center; padding: 16px 0 8px 0; }
  .disclaimer { font-size: 0.82em; color: #888; text-align: center; }
"""


# ─────────────────────────────────────────────────────────────────────────────
# GRADIO UI
# ─────────────────────────────────────────────────────────────────────────────

def build_ui() -> gr.Blocks:
    ollama_models  = _get_ollama_models()
    default_ollama = ollama_cfg.model if ollama_cfg.model in ollama_models else (
        ollama_models[0] if ollama_models else "medllama2:latest"
    )

    with gr.Blocks(title="🏥 Whisper Summer School — EMR Demo") as demo:

        # ── Header ────────────────────────────────────────────────────────────
        gr.HTML("""
          <div class="header-box">
            <h1>🏥 Whisper Summer School</h1>
            <p>Medical Transcription &amp; SOAP Note Generator</p>
            <p class="disclaimer">
              ⚠️ Output AI bersifat <em>advisory</em>.
              Wajib ditinjau tenaga medis sebelum digunakan secara klinis.
            </p>
          </div>
        """)

        # ── Layout Utama ──────────────────────────────────────────────────────
        with gr.Row():

            # ── Kolom Kiri: Konfigurasi ───────────────────────────────────────
            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Konfigurasi")

                # ✅ Microphone fix: info banner
                gr.HTML("""
                  <div style="
                    background:#e8f4fd; border:1px solid #90caf9;
                    border-radius:8px; padding:8px 12px;
                    font-size:0.82em; color:#1565c0; margin-bottom:6px;">
                    🎙️ <strong>Mikrofon:</strong> Pastikan buka via
                    <code>http://localhost:PORT</code> — bukan
                    <code>http://0.0.0.0:PORT</code>
                  </div>
                """)

                audio_input = gr.Audio(
                    label="🎙️ Upload Audio / Rekam Mikrofon",
                    type="filepath",
                    sources=["upload", "microphone"],
                )

                with gr.Group():
                    backend_radio = gr.Radio(
                        label="🤖 Backend LLM",
                        choices=["openmed", "ollama", "hf"],
                        value=BACKEND.lower(),
                        info="OpenMed = NER lokal | Ollama = model chat | hf = HuggingFace",
                    )
                    ollama_model_dd = gr.Dropdown(
                        label="🦙 Model Ollama",
                        choices=ollama_models,
                        value=default_ollama,
                        visible=(BACKEND.lower() == "ollama"),
                        interactive=True,
                        info="Hanya aktif jika backend = ollama",
                    )
                    refresh_btn = gr.Button(
                        "🔄 Refresh model Ollama",
                        size="sm",
                        visible=(BACKEND.lower() == "ollama"),
                    )

                with gr.Group():
                    whisper_dd = gr.Dropdown(
                        label="🎙️ Whisper Model",
                        choices=["tiny", "base", "small", "medium", "large-v3-turbo"],
                        value=whisper_cfg.model_size,
                        info="Lebih besar = lebih akurat, lebih lambat",
                    )
                    lang_dd = gr.Dropdown(
                        label="🌐 Bahasa",
                        choices=["id", "en", "auto"],
                        value=whisper_cfg.language,
                        info="auto = deteksi otomatis",
                    )

                with gr.Group():
                    skip_soap_cb = gr.Checkbox(
                        label="⏭️ Skip SOAP (transkripsi saja)",
                        value=False,
                    )
                    deidentify_cb = gr.Checkbox(
                        label="🔒 De-identifikasi PII (OpenMed)",
                        value=openmed_cfg.deidentify_before_soap,
                        info="Mask nama & data sensitif sebelum diproses",
                    )

                run_btn = gr.Button(
                    "▶️ Jalankan Pipeline",
                    variant="primary",
                    size="lg",
                )

            # ── Kolom Kanan: Output ───────────────────────────────────────────
            with gr.Column(scale=2):
                gr.Markdown("### 📊 Output")

                with gr.Tabs():

                    with gr.Tab("📝 Transkrip"):
                        transcript_out = gr.Textbox(
                            label="Hasil Transkripsi Whisper",
                            lines=14,
                            placeholder="Transkrip akan muncul di sini...",
                        )
                        dl_transcript_out = gr.File(
                            label="⬇️ Download Transkrip (.txt)",
                            visible=False,
                        )

                    with gr.Tab("📋 SOAP Note"):
                        soap_text_out = gr.Textbox(
                            label="Catatan SOAP",
                            lines=20,
                            placeholder="SOAP note akan muncul di sini...",
                        )
                        with gr.Row():
                            dl_soap_txt_out = gr.File(
                                label="⬇️ Download SOAP (.txt)",
                                visible=False,
                            )
                            dl_soap_json_out = gr.File(
                                label="⬇️ Download SOAP (.json)",
                                visible=False,
                            )

                    with gr.Tab("🗂️ JSON"):
                        soap_json_out = gr.Code(
                            label="SOAP (JSON)",
                            language="json",
                            lines=20,
                        )

                    with gr.Tab("📟 Log"):
                        log_out = gr.Textbox(
                            label="Pipeline Log",
                            lines=20,
                            placeholder="Log proses akan muncul di sini...",
                        )

        # ── Footer: Device Info ───────────────────────────────────────────────
        gr.HTML(f"""
          <div style="text-align:center; margin-top:8px; font-size:0.85em; color:#666;">
            Hardware: <strong>{_device_label()}</strong> &nbsp;|&nbsp;
            Whisper: <strong>{whisper_cfg.model_size}</strong> &nbsp;|&nbsp;
            Backend: <strong>{BACKEND}</strong> &nbsp;|&nbsp;
            🎙️ Mic: buka via <strong>http://localhost</strong>
          </div>
        """)

        # ── Events ────────────────────────────────────────────────────────────
        def toggle_ollama(backend: str):
            is_ollama = backend == "ollama"
            return gr.update(visible=is_ollama), gr.update(visible=is_ollama)

        backend_radio.change(
            fn=toggle_ollama,
            inputs=backend_radio,
            outputs=[ollama_model_dd, refresh_btn],
        )

        def refresh_ollama():
            models = _get_ollama_models()
            return gr.update(choices=models, value=models[0] if models else "medllama2:latest")

        refresh_btn.click(fn=refresh_ollama, outputs=ollama_model_dd)

        def _show_downloads(log, transcript, soap_text, soap_json,
                            dl_transcript, dl_soap_txt, dl_soap_json):
            return (
                log, transcript, soap_text, soap_json,
                gr.update(value=dl_transcript, visible=bool(dl_transcript)),
                gr.update(value=dl_soap_txt,   visible=bool(dl_soap_txt)),
                gr.update(value=dl_soap_json,  visible=bool(dl_soap_json)),
            )

        run_btn.click(
            fn=run_pipeline,
            inputs=[
                audio_input, backend_radio, ollama_model_dd,
                whisper_dd, lang_dd, skip_soap_cb, deidentify_cb,
            ],
            outputs=[
                log_out, transcript_out, soap_text_out, soap_json_out,
                dl_transcript_out, dl_soap_txt_out, dl_soap_json_out,
            ],
        ).then(
            fn=_show_downloads,
            inputs=[
                log_out, transcript_out, soap_text_out, soap_json_out,
                dl_transcript_out, dl_soap_txt_out, dl_soap_json_out,
            ],
            outputs=[
                log_out, transcript_out, soap_text_out, soap_json_out,
                dl_transcript_out, dl_soap_txt_out, dl_soap_json_out,
            ],
        )

    return demo


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import socket

    # ── Deteksi port kosong mulai dari 7860 ───────────────────────────────────
    def _find_free_port(start: int = 7860, end: int = 7880) -> int:
        for port in range(start, end + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", port)) != 0:
                    return port
        return start  # fallback

    port = int(os.environ.get("GRADIO_SERVER_PORT", _find_free_port()))

    print(f"\n{'='*55}")
    print(f"  🏥  Whisper Summer School — EMR Demo")
    print(f"{'='*55}")
    print(f"  🌐  Buka di browser : http://localhost:{port}")
    print(f"  🎙️   Mikrofon        : ✅ aktif (localhost = secure context)")
    print(f"  ⚠️   JANGAN buka via : http://0.0.0.0:{port}  (mic tidak aktif)")
    print(f"{'='*55}\n")

    demo = build_ui()
    demo.launch(
        server_name="127.0.0.1",   # ✅ KUNCI: localhost = secure context
        server_port=port,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
        css=_CSS,
    )
