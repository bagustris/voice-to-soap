"""
soap_openmed.py — Generate catatan SOAP medis menggunakan OpenMed v1.6+.

Pipeline:
  1. De-identifikasi PII dari transkrip (opsional)
  2. Ekstraksi entitas klinis via analyze_text (NER)
  3. Susun catatan SOAP terstruktur dari entitas
"""

from __future__ import annotations

import json
import os
import sys
import glob
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

# ── OpenMed imports — robust terhadap perubahan API ──────────────────────────
OPENMED_AVAILABLE      = False
OPENMED_CLINICAL_AVAIL = False
_openmed_version       = "unknown"

try:
    import openmed
    from openmed import analyze_text, deidentify
    OPENMED_AVAILABLE = True
    _openmed_version  = getattr(openmed, "__version__", "unknown")

    # Coba import clinical — API bisa berbeda antar versi
    try:
        from openmed.clinical import assert_context_axes
        OPENMED_CLINICAL_AVAIL = True
        _context_fn = assert_context_axes
    except ImportError:
        # v1.6+ mungkin pakai nama lain — cek dinamis
        import openmed.clinical as _clin
        _clin_attrs = dir(_clin)

        # Cari fungsi context analysis dengan nama alternatif
        _ctx_candidates = [
            "assert_context", "context_assert", "analyze_context",
            "get_context", "context_axes", "clinical_context",
        ]
        _found_ctx = None
        for _name in _ctx_candidates:
            if _name in _clin_attrs:
                _found_ctx = getattr(_clin, _name)
                break

        if _found_ctx:
            OPENMED_CLINICAL_AVAIL = True
            _context_fn = _found_ctx
        else:
            # Tidak ada fungsi context — pakai dummy
            OPENMED_CLINICAL_AVAIL = False
            _context_fn = None

except ImportError:
    pass

if not OPENMED_AVAILABLE:
    print("⚠️  openmed tidak terinstall.")
    print("    Jalankan: pip install 'openmed[mlx]'  (Apple Silicon)")
    print("              pip install openmed          (CPU/NVIDIA)\n")
else:
    ctx_status = "✅" if OPENMED_CLINICAL_AVAIL else "⚠️  (context analysis tidak tersedia)"
    print(f"✅ OpenMed v{_openmed_version} terdeteksi | Clinical NER: {ctx_status}")

from config import openmed_cfg, output_cfg


# ─────────────────────────────────────────────────────────────────────────────
# DATA CLASS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SOAPNote:
    subjective:  str = ""
    objective:   str = ""
    assessment:  str = ""
    plan:        str = ""
    raw_entities: list = field(default_factory=list)
    deidentified_text: Optional[str] = None
    pii_detected: bool = False
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    model_used: str = ""
    warning: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    def to_text(self) -> str:
        lines = [
            "=" * 55,
            "         CATATAN MEDIS — FORMAT SOAP",
            f"  Dibuat : {self.generated_at}",
            f"  Model  : {self.model_used}",
            "=" * 55,
        ]
        if self.pii_detected:
            lines.append("  🔒 PII terdeteksi dan telah di-de-identifikasi")
            lines.append("-" * 55)
        if self.warning:
            lines.append(f"  ⚠️  {self.warning}")
            lines.append("-" * 55)

        sections = {
            "S — Subjective (Keluhan Pasien)": self.subjective,
            "O — Objective (Temuan Klinis)":   self.objective,
            "A — Assessment (Penilaian)":       self.assessment,
            "P — Plan (Rencana Tindakan)":      self.plan,
        }
        for title, content in sections.items():
            lines.append(f"\n[{title}]")
            lines.append(content if content.strip() else "  (tidak tersedia)")

        lines.append("\n" + "=" * 55)
        lines.append("  ⚠️  DISCLAIMER: Output ini bersifat advisory.")
        lines.append("  Tidak untuk digunakan sebagai keputusan klinis.")
        lines.append("=" * 55)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


# ─────────────────────────────────────────────────────────────────────────────
# LABEL → SOAP MAPPING
# ─────────────────────────────────────────────────────────────────────────────

_LABEL_TO_SOAP: dict[str, str] = {
    "SYMPTOM": "S", "SIGN": "S", "COMPLAINT": "S",
    "PAIN": "S", "HISTORY": "S",
    "VITAL_SIGN": "O", "LAB_VALUE": "O", "MEASUREMENT": "O",
    "FINDING": "O", "PROCEDURE": "O", "ANATOMY": "O",
    "DISEASE": "A", "DISORDER": "A", "CONDITION": "A",
    "DIAGNOSIS": "A", "CANCER": "A", "SYNDROME": "A",
    "MEDICATION": "P", "DRUG": "P", "TREATMENT": "P",
    "THERAPY": "P", "DOSAGE": "P", "FOLLOW_UP": "P", "REFERRAL": "P",
}

def _map_entity_to_soap(label: str) -> str:
    return _LABEL_TO_SOAP.get(label.upper(), "S")


# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT ANALYSIS — graceful fallback jika tidak tersedia
# ─────────────────────────────────────────────────────────────────────────────

def _get_context(entity_text: str, window_text: str) -> dict:
    """
    Analisis konteks klinis (negasi, temporalitas, kepastian).
    Fallback ke rule-based sederhana jika API tidak tersedia.
    """
    if OPENMED_CLINICAL_AVAIL and _context_fn is not None:
        try:
            result = _context_fn(entity_text, window_text)
            if hasattr(result, "to_dict"):
                return result.to_dict()
            elif isinstance(result, dict):
                return result
        except Exception:
            pass

    # ── Rule-based fallback ───────────────────────────────────────────────────
    text_lower = window_text.lower()
    negation   = "negated" if any(
        cue in text_lower for cue in [
            "no ", "not ", "without", "denied", "denies", "absent",
            "tidak", "bukan", "tanpa", "menyangkal",
        ]
    ) else "affirmed"

    temporality = "historical" if any(
        cue in text_lower for cue in [
            "history of", "previously", "past", "former", "s/p",
            "riwayat", "dahulu", "sebelumnya", "pernah",
        ]
    ) else "recent"

    certainty = "uncertain" if any(
        cue in text_lower for cue in [
            "possible", "probable", "rule out", "suspect", "likely",
            "kemungkinan", "curiga", "mungkin", "suspect",
        ]
    ) else "certain"

    return {
        "negation":    negation,
        "temporality": temporality,
        "certainty":   certainty,
    }


def _extract_window(entity_text: str, full_text: str, window: int = 60) -> str:
    """Ambil teks sebelum entitas sebagai konteks."""
    idx = full_text.lower().find(entity_text.lower())
    if idx < 0:
        return full_text[:window]
    return full_text[max(0, idx - window): idx]


# ─────────────────────────────────────────────────────────────────────────────
# CORE: EKSTRAKSI ENTITAS
# ─────────────────────────────────────────────────────────────────────────────

def _extract_entities(text: str) -> list[dict]:
    """Ekstraksi entitas klinis via OpenMed analyze_text."""
    if not OPENMED_AVAILABLE:
        raise RuntimeError("openmed tidak tersedia")

    # Coba berbagai signature analyze_text (API bisa beda antar versi)
    result = None
    errors = []

    # Signature v1.6+ — minimal args
    try:
        result = analyze_text(text=text, model_name=openmed_cfg.ner_model)
    except TypeError as e:
        errors.append(f"signature v1: {e}")

    # Signature dengan config object
    if result is None:
        try:
            from openmed import OpenMedConfig
            cfg    = OpenMedConfig(device=openmed_cfg.device)
            result = analyze_text(
                text=text,
                model_name=openmed_cfg.ner_model,
                config=cfg,
            )
        except Exception as e:
            errors.append(f"signature v2: {e}")

    # Signature lengkap
    if result is None:
        try:
            result = analyze_text(
                text=text,
                model_name=openmed_cfg.ner_model,
                aggregation_strategy="simple",
                output_format="dict",
                include_confidence=True,
                confidence_threshold=0.55,
            )
        except Exception as e:
            errors.append(f"signature v3: {e}")

    if result is None:
        raise RuntimeError(f"analyze_text gagal: {errors}")

    # ── Normalisasi hasil ─────────────────────────────────────────────────────
    # result bisa berupa object dengan .entities atau list langsung
    raw_entities = []
    if hasattr(result, "entities"):
        raw_entities = result.entities
    elif isinstance(result, list):
        raw_entities = result
    elif isinstance(result, dict):
        raw_entities = result.get("entities", [])

    entities = []
    for ent in raw_entities:
        # Handle dict atau object
        if isinstance(ent, dict):
            word  = ent.get("word", ent.get("text", ""))
            label = ent.get("entity_group", ent.get("label", ent.get("entity", "UNKNOWN")))
            score = ent.get("score", ent.get("confidence", 0.0))
        else:
            word  = getattr(ent, "word",  getattr(ent, "text",  ""))
            label = getattr(ent, "entity_group", getattr(ent, "label", "UNKNOWN"))
            score = getattr(ent, "score", getattr(ent, "confidence", 0.0))

        if not word:
            continue

        window  = _extract_window(word, text)
        context = _get_context(word, window)

        entities.append({
            "text":         word,
            "label":        label,
            "confidence":   round(float(score), 4),
            "soap_section": _map_entity_to_soap(label),
            "context":      context,
        })

    return entities


# ─────────────────────────────────────────────────────────────────────────────
# CORE: DE-IDENTIFIKASI PII
# ─────────────────────────────────────────────────────────────────────────────

def _deidentify_transcript(transcript: str) -> tuple[str, bool]:
    if not OPENMED_AVAILABLE:
        return transcript, False
    try:
        result    = deidentify(transcript, method=openmed_cfg.deidentify_method)
        # Handle berbagai return type
        if hasattr(result, "deidentified_text"):
            clean     = result.deidentified_text
            n_pii     = len(result.entities) if hasattr(result, "entities") else 0
        elif isinstance(result, dict):
            clean     = result.get("deidentified_text", transcript)
            n_pii     = len(result.get("entities", []))
        elif isinstance(result, str):
            clean     = result
            n_pii     = 1 if clean != transcript else 0
        else:
            return transcript, False

        pii_found = n_pii > 0 or clean != transcript
        if pii_found:
            print(f"  🔒 PII terdeteksi: {n_pii} entitas → di-de-identifikasi")
        return clean, pii_found

    except Exception as e:
        print(f"  ⚠️  De-identifikasi gagal: {e} — lanjut tanpa de-id")
        return transcript, False


# ─────────────────────────────────────────────────────────────────────────────
# FALLBACK: RULE-BASED BILINGUAL
# ─────────────────────────────────────────────────────────────────────────────

_SOAP_KEYWORDS = {
    "S": {
        "en": [
            "dizziness", "dizzy", "vertigo", "headache", "nausea", "vomiting",
            "pain", "ache", "discomfort", "fatigue", "tired", "weakness",
            "ringing", "tinnitus", "hearing loss", "blurred vision", "shortness",
            "chest pain", "palpitation", "fever", "cough", "sore throat",
            "symptom", "feel", "feeling", "experience", "suffer",
            "been having", "i've been", "for a few", "for several",
            "come and go", "episodes", "attacks",
        ],
        "id": [
            "keluhan", "sakit", "nyeri", "demam", "batuk", "sesak", "pusing",
            "mual", "muntah", "lemas", "berputar", "telinga berdenging",
            "pendengaran", "mengeluh", "merasakan", "sudah beberapa",
        ],
    },
    "O": {
        "en": [
            "blood pressure", "heart rate", "pulse", "temperature", "weight",
            "height", "bmi", "oxygen", "saturation", "examination", "looks",
            "appears", "comfortable", "alert", "oriented",
            "lab", "result", "test", "scan", "mri", "ct", "x-ray",
            "ekg", "ecg", "finding", "blood test", "normal",
        ],
        "id": [
            "tekanan darah", "nadi", "suhu", "berat badan", "pemeriksaan",
            "hasil", "lab", "vital", "tampak", "terlihat",
        ],
    },
    "A": {
        "en": [
            "diagnosis", "diagnose", "consistent with", "impression",
            "condition", "disorder", "disease", "syndrome",
            "migraine", "vertigo", "meniere", "hypertension", "diabetes",
            "infection", "inflammation", "it looks like", "caused by",
            "this is caused", "buildup", "pressure",
        ],
        "id": [
            "diagnosis", "diagnosa", "didiagnosis", "menderita",
            "kemungkinan", "curiga", "mengarah", "disebabkan",
        ],
    },
    "P": {
        "en": [
            "prescribe", "prescription", "medication", "medicine", "drug",
            "tablet", "capsule", "mg", "dose", "dosage", "twice", "daily",
            "refer", "referral", "follow up", "follow-up",
            "recommend", "advise", "treatment", "therapy",
            "i'd like to", "i would like to", "we will", "send that",
            "prochlorperazine", "betahistine", "antihistamine", "pharmacy",
        ],
        "id": [
            "obat", "resep", "terapi", "rujuk", "kontrol", "rawat",
            "diberikan", "diminta", "disarankan", "tindakan",
        ],
    },
}

# Kalimat yang harus di-skip (noise / bukan klinis)
_SKIP_PATTERNS = [
    "nice to meet", "completed our ai assessment", "i would agree with our ai",
    "so i can see you've completed", "are you allergic",
]

def _detect_language(text: str) -> str:
    en_markers = ["the ", "and ", "you ", "have ", "been ", "with ", "that ",
                  "this ", "your ", "for ", "are ", "can ", " i ", " it "]
    id_markers = ["yang ", "dan ", "dengan ", "untuk ", "saya ", "anda ",
                  "ini ", "itu ", "pada ", "dari ", "tidak ", "sudah "]
    text_lower = text.lower()
    en_score   = sum(text_lower.count(m) for m in en_markers)
    id_score   = sum(text_lower.count(m) for m in id_markers)
    return "en" if en_score >= id_score else "id"


def _fallback_rule_based_soap(transcript: str) -> dict[str, str]:
    print("  ℹ️  Menggunakan fallback rule-based SOAP (bilingual EN+ID)...")
    import re

    lang = _detect_language(transcript)
    print(f"  🌐 Bahasa terdeteksi: {'English' if lang == 'en' else 'Indonesia'}")

    sentences = re.split(r'(?<=[.!?])\s+', transcript.strip())
    buckets: dict[str, list[str]] = {"S": [], "O": [], "A": [], "P": []}

    for sent in sentences:
        sent = sent.strip()
        if len(sent) < 15:
            continue

        sent_lower = sent.lower()

        # Skip kalimat noise
        if any(skip in sent_lower for skip in _SKIP_PATTERNS):
            continue

        scores = {"S": 0, "O": 0, "A": 0, "P": 0}
        for section, lang_kws in _SOAP_KEYWORDS.items():
            for kw_lang in ("en", "id"):
                weight = 2 if kw_lang == lang else 1
                for kw in lang_kws[kw_lang]:
                    if kw in sent_lower:
                        scores[section] += weight

        best_section = max(scores, key=scores.get)
        best_score   = scores[best_section]

        if best_score > 0:
            buckets[best_section].append(f"• {sent}")

    def fmt(items: list[str]) -> str:
        return "\n".join(items) if items else "  (tidak terdeteksi dari transkrip)"

    total = sum(len(v) for v in buckets.values())
    print(f"  📊 Kalimat terklasifikasi: {total} "
          f"(S:{len(buckets['S'])} O:{len(buckets['O'])} "
          f"A:{len(buckets['A'])} P:{len(buckets['P'])})")

    return {"S": fmt(buckets["S"]), "O": fmt(buckets["O"]),
            "A": fmt(buckets["A"]), "P": fmt(buckets["P"])}


# ─────────────────────────────────────────────────────────────────────────────
# BUILD SOAP DARI ENTITAS
# ─────────────────────────────────────────────────────────────────────────────

def _build_soap_from_entities(entities: list[dict], transcript: str) -> dict[str, str]:
    buckets: dict[str, list[str]] = {"S": [], "O": [], "A": [], "P": []}

    for ent in entities:
        ctx         = ent.get("context", {})
        negation    = ctx.get("negation", "affirmed")
        temporality = ctx.get("temporality", "recent")
        certainty   = ctx.get("certainty", "certain")
        section     = ent["soap_section"]
        text        = ent["text"]
        conf        = ent["confidence"]

        if negation == "negated":
            continue

        prefix = ""
        if temporality == "historical":
            prefix = "[Riwayat] "
        elif certainty == "uncertain":
            prefix = "[Kemungkinan] "

        label_str = ent["label"].replace("_", " ").title()
        buckets[section].append(f"• {prefix}{text} ({label_str}, conf: {conf:.0%})")

    if not any(buckets.values()):
        return _fallback_rule_based_soap(transcript)

    def fmt(items: list[str]) -> str:
        return "\n".join(items) if items else "  (tidak terdeteksi dari transkrip)"

    return {"S": fmt(buckets["S"]), "O": fmt(buckets["O"]),
            "A": fmt(buckets["A"]), "P": fmt(buckets["P"])}


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_soap(transcript: str) -> SOAPNote:
    """Entry point utama: terima transkrip → kembalikan SOAPNote."""
    print("\n📋 Memulai generasi SOAP via OpenMed...")

    if not transcript or not transcript.strip():
        return SOAPNote(warning="Transkrip kosong.")

    # ── Step 1: De-identifikasi ───────────────────────────────────────────────
    clean_text   = transcript
    pii_detected = False

    if openmed_cfg.deidentify_before_soap:
        print("  🔒 Step 1/3: De-identifikasi PII...")
        clean_text, pii_detected = _deidentify_transcript(transcript)
    else:
        print("  ⏭️  Step 1/3: De-identifikasi dilewati (nonaktif di config)")

    # ── Step 2: NER ───────────────────────────────────────────────────────────
    print(f"  🔍 Step 2/3: Ekstraksi entitas klinis ({openmed_cfg.ner_model})...")
    entities = []
    warning  = ""

    if OPENMED_AVAILABLE:
        try:
            entities = _extract_entities(clean_text)
            ctx_note = "" if OPENMED_CLINICAL_AVAIL else " (context: rule-based)"
            print(f"  ✅ {len(entities)} entitas ditemukan{ctx_note}")
        except Exception as e:
            warning = f"NER gagal: {e}"
            print(f"  ⚠️  {warning}")
    else:
        warning = "OpenMed tidak tersedia — menggunakan fallback rule-based bilingual."
        print(f"  ⚠️  {warning}")

    # ── Step 3: Susun SOAP ────────────────────────────────────────────────────
    print("  📝 Step 3/3: Menyusun catatan SOAP...")
    soap_sections = _build_soap_from_entities(entities, clean_text)

    used_model = openmed_cfg.ner_model
    if not entities:
        used_model += " (fallback rule-based)"
    elif not OPENMED_CLINICAL_AVAIL:
        used_model += " (context: rule-based)"

    note = SOAPNote(
        subjective        = soap_sections["S"],
        objective         = soap_sections["O"],
        assessment        = soap_sections["A"],
        plan              = soap_sections["P"],
        raw_entities      = entities,
        deidentified_text = clean_text if pii_detected else None,
        pii_detected      = pii_detected,
        model_used        = used_model,
        warning           = warning,
    )

    print("  ✅ SOAP selesai dibuat!\n")
    return note
