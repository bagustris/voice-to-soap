import ollama
import json
import re
from datetime import datetime

# Model terkecil yang tersedia
MEDICAL_MODEL = "biomistral"   # ~4.5GB Q4_K_M
# Alternatif: "medllama2"      # ~3.8GB jika biomistral terlalu besar

SOAP_PROMPT_TEMPLATE = """You are a clinical documentation assistant. 
Based on the following doctor-patient conversation transcript, generate a structured SOAP note.

TRANSCRIPT:
{transcript}

Generate a SOAP note in the following JSON format:
{{
  "subjective": {{
    "chief_complaint": "...",
    "history_of_present_illness": "...",
    "review_of_systems": "..."
  }},
  "objective": {{
    "vital_signs": "...",
    "physical_examination": "...",
    "lab_results": "..."
  }},
  "assessment": {{
    "diagnosis": "...",
    "differential_diagnosis": "..."
  }},
  "plan": {{
    "treatment": "...",
    "medications": "...",
    "follow_up": "..."
  }}
}}

Respond ONLY with valid JSON. No extra text."""


def generate_soap_note(transcript: str, model: str = MEDICAL_MODEL) -> dict:
    """
    Generate SOAP note dari transkrip menggunakan BioMistral via Ollama.
    
    Args:
        transcript: Teks transkrip dokter-pasien
        model: Nama model Ollama yang digunakan
    
    Returns:
        dict berisi SOAP note terstruktur
    """
    print(f"🤖 Generating SOAP note dengan model: {model}")
    
    prompt = SOAP_PROMPT_TEMPLATE.format(transcript=transcript)

    try:
        response = ollama.chat(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical documentation expert. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.1,    # Rendah untuk konsistensi medis
                "num_predict": 1024,
            }
        )

        raw_response = response["message"]["content"]
        
        # Ekstrak JSON dari response
        json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
        if json_match:
            soap_dict = json.loads(json_match.group())
        else:
            raise ValueError("Model tidak mengembalikan JSON yang valid")

        print("✅ SOAP note berhasil dibuat!")
        return soap_dict

    except ollama.ResponseError as e:
        print(f"❌ Error Ollama: {e}")
        print(f"💡 Pastikan model '{model}' sudah di-pull: ollama pull {model}")
        raise
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
        print(f"Raw response: {raw_response}")
        raise


def save_soap_note(soap_dict: dict, output_path: str = None) -> str:
    """Simpan SOAP note ke file JSON dan TXT."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if output_path is None:
        output_path = f"outputs/soap_{timestamp}"

    # Simpan JSON
    json_path = f"{output_path}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(soap_dict, f, indent=2, ensure_ascii=False)
    
    # Simpan TXT yang readable
    txt_path = f"{output_path}.txt"
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("=" * 50 + "\n")
        f.write("         SOAP NOTE\n")
        f.write("=" * 50 + "\n\n")
        
        sections = {
            "SUBJECTIVE (S)": soap_dict.get("subjective", {}),
            "OBJECTIVE (O)": soap_dict.get("objective", {}),
            "ASSESSMENT (A)": soap_dict.get("assessment", {}),
            "PLAN (P)": soap_dict.get("plan", {})
        }
        
        for section_name, section_data in sections.items():
            f.write(f"[{section_name}]\n")
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
            else:
                f.write(f"  {section_data}\n")
            f.write("\n")

    print(f"💾 Disimpan: {json_path}")
    print(f"💾 Disimpan: {txt_path}")
    return txt_path


if __name__ == "__main__":
    # Test dengan transkrip contoh
    sample_transcript = """
    Dokter: Selamat pagi, apa yang membawa Anda ke sini hari ini?
    Pasien: Saya sudah batuk selama 3 hari, disertai demam dan sakit tenggorokan.
    Dokter: Apakah ada sesak napas atau nyeri dada?
    Pasien: Tidak ada sesak, tapi kepala saya terasa berat.
    Dokter: Baik, suhu Anda 38.5 derajat. Tenggorokan merah. Kemungkinan ISPA.
    """
    
    soap = generate_soap_note(sample_transcript)
    save_soap_note(soap)
    print(json.dumps(soap, indent=2, ensure_ascii=False))
