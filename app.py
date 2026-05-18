import streamlit as st
import asyncio
import edge_tts
from pydub import AudioSegment
import tempfile
import os
import shutil
import subprocess

# ===========================================================================
# NVIDIA PREMIUM — Optional import (no falla si no se instala)
# ===========================================================================
NVIDIA_AVAILABLE = False
try:
    import riva.client
    from riva.client.proto.riva_audio_pb2 import AudioEncoding
    import wave as _wave
    NVIDIA_AVAILABLE = True
except ImportError:
    pass

# ===========================================================================
# PAGE CONFIG
# ===========================================================================
st.set_page_config(page_title="VOICER v2.0", page_icon="🎙️", layout="centered")

# ===========================================================================
# CSS
# ===========================================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stButton>button {
        border-radius: 8px; font-weight: 600; transition: all 0.3s ease;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); color: white; border: none;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(99,102,241,0.4); }
    [data-testid="stVerticalBlock"] { overflow: visible !important; }
    .stSelectbox [data-baseweb="popover"] { z-index: 999999 !important; }
    .stSelectbox [role="listbox"] { z-index: 999999 !important; }
</style>
""", unsafe_allow_html=True)

# ===========================================================================
# API KEY — Streamlit Cloud usa st.secrets, local usa env
# ===========================================================================
NVIDIA_API_KEY = st.secrets.get("NVIDIA_API_KEY", os.getenv("NVIDIA_API_KEY", "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"))
nvidia_ready = NVIDIA_AVAILABLE and bool(NVIDIA_API_KEY) and NVIDIA_API_KEY != "your_nvidia_api_key_here"

# ===========================================================================
# STATE
# ===========================================================================
if 'blocks' not in st.session_state:
    st.session_state.blocks = [{"id": 0}]
if 'block_counter' not in st.session_state:
    st.session_state.block_counter = 1

def add_block():
    st.session_state.blocks.append({"id": st.session_state.block_counter})
    st.session_state.block_counter += 1

def remove_block(block_id):
    st.session_state.blocks = [b for b in st.session_state.blocks if b["id"] != block_id]

# ===========================================================================
# TTS ENGINES
# ===========================================================================

async def _edge_generate(text, voice, output_path):
    """Genera audio con edge-tts (motor Estándar, siempre disponible)."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_edge_tts(text, voice, output_path):
    asyncio.run(_edge_generate(text, voice, output_path))


def generate_nvidia_tts(text: str, voice: str, output_path: str) -> bool:
    """Genera audio con NVIDIA Magpie TTS (Premium). Retorna True si ok, False si falla."""
    if not nvidia_ready:
        return False

    # Parsear language_code del voice_name: "Magpie-Multilingual.EN-US.Sofia" -> "en-US"
    parts = voice.split(".")
    if len(parts) >= 2:
        raw_lang = parts[1]
        lang_parts = raw_lang.split("-")
        lang_code = f"{lang_parts[0].lower()}-{lang_parts[1].upper()}" if len(lang_parts) == 2 else "en-US"
    else:
        lang_code = "en-US"

    # Mapeo de voces obsoletas
    obsolete = {
        "Magpie-Multilingual.EN-US.Isabella": "Magpie-Multilingual.EN-US.Isabela",
        "Magpie-Multilingual.EN-US.Emma": "Magpie-Multilingual.EN-US.Sofia",
        "Magpie-Multilingual.EN-US.Brian": "Magpie-Multilingual.EN-US.Jason",
        "English-US.Female-1": "Magpie-Multilingual.EN-US.Mia",
        "English-US.Female-2": "Magpie-Multilingual.EN-US.Sofia",
        "English-US.Male-1": "Magpie-Multilingual.EN-US.Diego",
    }
    voice = obsolete.get(voice, voice)

    try:
        auth = riva.client.Auth(
            uri="grpc.nvcf.nvidia.com:443",
            use_ssl=True,
            metadata_args=[
                ["function-id", "877104f7-e885-42b9-8de8-f6e4c6303969"],
                ["authorization", f"Bearer {NVIDIA_API_KEY}"],
            ]
        )
        service = riva.client.SpeechSynthesisService(auth)
        resp = service.synthesize(
            text=text,
            voice_name=voice,
            language_code=lang_code,
            sample_rate_hz=44100,
            encoding=AudioEncoding.LINEAR_PCM
        )

        # Guardar WAV
        wav_path = output_path.replace(".mp3", ".wav")
        with _wave.open(wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframesraw(resp.audio)

        # Convertir a MP3 con FFmpeg
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", output_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
        )

        try:
            os.remove(wav_path)
        except Exception:
            pass

        return os.path.exists(output_path)

    except Exception as e:
        st.error(f"Error NVIDIA: {e}")
        return False

# ===========================================================================
# UI — HEADER
# ===========================================================================
st.title("🎙️ Generador Bilingüe VOICER")
st.markdown("Crea inmersión bilingüe — v2.0 • 90 voces Neural • 320kbps")

# ===========================================================================
# ENGINE MODE SELECTOR
# ===========================================================================
st.divider()

if nvidia_ready:
    engine_mode = st.radio(
        "⚡ Motor de Síntesis",
        ["Estándar (Edge TTS)", "Premium (NVIDIA + Edge)"],
        horizontal=True,
        index=0,
        help="Estándar: todo con edge-tts (gratis). Premium: inglés con NVIDIA IA, español con edge-tts."
    )
    use_nvidia = engine_mode.startswith("Premium")
else:
    if not NVIDIA_AVAILABLE:
        st.info("💡 El motor NVIDIA no está disponible en este entorno. Usando modo Estándar (edge-tts).")
    elif not NVIDIA_API_KEY:
        st.warning("🔑 NVIDIA_API_KEY no configurada. Agregala en Secrets de Streamlit Cloud para activar el modo Premium.")
    engine_mode = "Estándar (Edge TTS)"
    use_nvidia = False

# ===========================================================================
# VOICE CATALOGS
# ===========================================================================
st.subheader("⚙️ Configuración de Voces")

# --- Español: SIEMPRE edge-tts (47 voces de 21 países) ---
es_voices = [
    "es-AR-ElenaNeural", "es-AR-TomasNeural",
    "es-BO-MarceloNeural", "es-BO-SofiaNeural",
    "es-CL-CatalinaNeural", "es-CL-LorenzoNeural",
    "es-CO-GonzaloNeural", "es-CO-SalomeNeural",
    "es-CR-JuanNeural", "es-CR-MariaNeural",
    "es-CU-BelkysNeural", "es-CU-ManuelNeural",
    "es-DO-EmilioNeural", "es-DO-RamonaNeural",
    "es-EC-AndreaNeural", "es-EC-LuisNeural",
    "es-ES-AlvaroNeural", "es-ES-ElviraNeural", "es-ES-XimenaNeural",
    "es-GQ-JavierNeural", "es-GQ-TeresaNeural",
    "es-GT-AndresNeural", "es-GT-MartaNeural",
    "es-HN-CarlosNeural", "es-HN-KarlaNeural",
    "es-MX-DaliaNeural", "es-MX-JorgeNeural",
    "es-NI-FedericoNeural", "es-NI-YolandaNeural",
    "es-PA-MargaritaNeural", "es-PA-RobertoNeural",
    "es-PE-AlexNeural", "es-PE-CamilaNeural",
    "es-PR-KarinaNeural", "es-PR-VictorNeural",
    "es-PY-MarioNeural", "es-PY-TaniaNeural",
    "es-SV-LorenaNeural", "es-SV-RodrigoNeural",
    "es-US-AlonsoNeural", "es-US-PalomaNeural",
    "es-UY-MateoNeural", "es-UY-ValentinaNeural",
    "es-VE-PaolaNeural", "es-VE-SebastianNeural",
]

# --- Inglés Premium: NVIDIA (10 voces oficiales) ---
nvidia_en_voices = [
    "Magpie-Multilingual.EN-US.Sofia",
    "Magpie-Multilingual.EN-US.Mia",
    "Magpie-Multilingual.EN-US.Aria",
    "Magpie-Multilingual.EN-US.Isabela",
    "Magpie-Multilingual.EN-US.Louise",
    "Magpie-Multilingual.EN-US.Diego",
    "Magpie-Multilingual.EN-US.Pascal",
    "Magpie-Multilingual.EN-US.Jason",
    "Magpie-Multilingual.EN-US.Leo",
    "Magpie-Multilingual.EN-US.Ray",
]

# --- Inglés Estándar: edge-tts (43 voces de 13 países) ---
edge_en_voices = [
    "en-AU-NatashaNeural", "en-AU-WilliamMultilingualNeural",
    "en-CA-ClaraNeural", "en-CA-LiamNeural",
    "en-GB-LibbyNeural", "en-GB-MaisieNeural", "en-GB-RyanNeural",
    "en-GB-SoniaNeural", "en-GB-ThomasNeural",
    "en-HK-SamNeural", "en-HK-YanNeural",
    "en-IE-ConnorNeural", "en-IE-EmilyNeural",
    "en-IN-NeerjaExpressiveNeural", "en-IN-NeerjaNeural", "en-IN-PrabhatNeural",
    "en-KE-AsiliaNeural", "en-KE-ChilembaNeural",
    "en-NG-AbeoNeural", "en-NG-EzinneNeural",
    "en-NZ-MitchellNeural", "en-NZ-MollyNeural",
    "en-PH-JamesNeural", "en-PH-RosaNeural",
    "en-SG-LunaNeural", "en-SG-WayneNeural",
    "en-TZ-ElimuNeural", "en-TZ-ImaniNeural",
    "en-US-AnaNeural", "en-US-AndrewMultilingualNeural", "en-US-AndrewNeural",
    "en-US-AriaNeural", "en-US-AvaMultilingualNeural", "en-US-AvaNeural",
    "en-US-BrianMultilingualNeural", "en-US-BrianNeural", "en-US-ChristopherNeural",
    "en-US-EmmaMultilingualNeural", "en-US-EmmaNeural", "en-US-EricNeural",
    "en-US-GuyNeural", "en-US-JennyNeural", "en-US-MichelleNeural",
    "en-US-RogerNeural", "en-US-SteffanNeural",
    "en-ZA-LeahNeural", "en-ZA-LukeNeural",
]

# Seleccionar catálogo según modo
en_voices = nvidia_en_voices if use_nvidia else edge_en_voices

# Default voice según modo
default_en = nvidia_en_voices[0] if use_nvidia else "en-US-JennyNeural"
en_default_index = en_voices.index(default_en) if default_en in en_voices else 0

col1, col2 = st.columns(2)
with col1:
    es_voice = st.selectbox("Voz en Español", es_voices)
with col2:
    en_voice = st.selectbox(
        "Voz en Inglés",
        en_voices,
        index=en_default_index,
        help="NVIDIA Magpie IA" if use_nvidia else "Edge TTS Neural"
    )

if use_nvidia:
    st.caption("🎯 Modo Premium: español con edge-tts, inglés con NVIDIA Magpie IA")

st.divider()

# ===========================================================================
# GLOBAL PAUSE
# ===========================================================================
st.subheader("⏱️ Configuración Global")
global_pause_sec = st.slider("Pausa de Transición entre Bloques (segundos)", min_value=0.0, max_value=10.0, value=1.0, step=0.5, key="global_pause")

st.divider()

# ===========================================================================
# DYNAMIC BLOCKS
# ===========================================================================
st.subheader("📝 Bloques de Frases")

for i, block in enumerate(st.session_state.blocks):
    b_id = block["id"]
    with st.container(border=True):
        st.markdown(f"**Bloque {i + 1}**")
        c1, c2 = st.columns(2)
        with c1:
            st.text_area("Frase en Español", height=68, key=f"es_{b_id}")
        with c2:
            st.text_area("Frase en Inglés", height=68, key=f"en_{b_id}")
        c_silence, c_rep, c_btn = st.columns([2, 2, 1])
        with c_silence:
            st.slider("Silencio interno (segundos)", min_value=0.0, max_value=10.0, value=2.0, step=0.5, key=f"sil_{b_id}")
        with c_rep:
            st.number_input("Repeticiones en Inglés", min_value=1, max_value=5, value=1, step=1, key=f"rep_{b_id}")
        with c_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("❌ Eliminar", key=f"del_{b_id}"):
                remove_block(b_id)
                st.rerun()

st.button("➕ Añadir nueva frase", on_click=add_block, use_container_width=True)

st.divider()

# ===========================================================================
# GENERATION LOGIC
# ===========================================================================
if st.button("🚀 Generar Audio Final", type="primary", use_container_width=True):
    has_text = any(st.session_state.get(f"es_{b['id']}") or st.session_state.get(f"en_{b['id']}") for b in st.session_state.blocks)

    if not has_text:
        st.warning("⚠️ Añade al menos una frase en algún bloque antes de generar.")
    else:
        with st.spinner('Generando tu pista de inmersión...'):
            final_audio = AudioSegment.empty()
            audio_fr, audio_sw, audio_ch = 24000, 2, 1
            temp_dir_str = tempfile.mkdtemp()

            try:
                for i, block in enumerate(st.session_state.blocks):
                    b_id = block["id"]
                    text_es = st.session_state.get(f"es_{b_id}", "").strip()
                    text_en = st.session_state.get(f"en_{b_id}", "").strip()

                    if not text_es and not text_en:
                        continue

                    custom_silence_sec = st.session_state.get(f"sil_{b_id}", 2.0)
                    repetitions_en = st.session_state.get(f"rep_{b_id}", 1)
                    st.write(f"Procesando bloque {i + 1}...")

                    # --- Helpers de audio ---
                    def make_silence(seconds):
                        return AudioSegment.silent(
                            duration=int(seconds * 1000),
                            frame_rate=audio_fr
                        ).set_sample_width(audio_sw).set_channels(audio_ch)

                    def load_mp3(path):
                        seg = AudioSegment.from_mp3(path)
                        if seg.frame_rate != audio_fr:
                            seg = seg.set_frame_rate(audio_fr)
                        if seg.sample_width != audio_sw:
                            seg = seg.set_sample_width(audio_sw)
                        if seg.channels != audio_ch:
                            seg = seg.set_channels(audio_ch)
                        return seg

                    # --- 1. Audio en Español (SIEMPRE edge-tts) ---
                    if text_es:
                        temp_es = os.path.join(temp_dir_str, f"es_{b_id}.mp3")
                        generate_edge_tts(text_es, es_voice, temp_es)
                        audio_es = load_mp3(temp_es)
                        final_audio += audio_es
                        del audio_es
                        if custom_silence_sec > 0:
                            final_audio += make_silence(custom_silence_sec)

                    # --- 2. Audio en Inglés (engine según modo) ---
                    if text_en:
                        temp_en = os.path.join(temp_dir_str, f"en_{b_id}.mp3")

                        if use_nvidia:
                            ok = generate_nvidia_tts(text_en, en_voice, temp_en)
                            if not ok:
                                st.warning(f"⚠️ Falló NVIDIA en bloque {i+1}. Reintentando con edge-tts...")
                                generate_edge_tts(text_en, en_voice, temp_en)
                        else:
                            generate_edge_tts(text_en, en_voice, temp_en)

                        audio_en = load_mp3(temp_en)
                        for r in range(repetitions_en):
                            final_audio += audio_en
                            if custom_silence_sec > 0:
                                final_audio += make_silence(custom_silence_sec)
                        del audio_en

                    # --- 3. Pausa Global entre bloques ---
                    global_pause_val = st.session_state.get("global_pause", 1.0)
                    if global_pause_val > 0:
                        final_audio += make_silence(global_pause_val)

                st.write("Ensamblando pista final...")
                output_filename = "output_final.mp3"
                final_audio.export(output_filename, format="mp3", bitrate="320k")

            finally:
                try:
                    shutil.rmtree(temp_dir_str, ignore_errors=True)
                except Exception as e:
                    print(f"Error limpiando directorio: {e}")

        st.success("✅ Generación completada")

        with open(output_filename, "rb") as file:
            audio_bytes = file.read()

        st.audio(audio_bytes, format="audio/mp3")
        st.download_button(
            label="💾 Descargar output_final.mp3",
            data=audio_bytes,
            file_name=output_filename,
            mime="audio/mp3",
            use_container_width=True
        )
