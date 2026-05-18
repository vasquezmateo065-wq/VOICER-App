import streamlit as st
import asyncio
import edge_tts
from pydub import AudioSegment
import tempfile
import os
import shutil

# --- Configuración de la página ---
st.set_page_config(page_title="VOICER v2.0", page_icon="🎙️", layout="centered")

# --- Estilos CSS Premium ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        color: white;
        border: none;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
    }
    
    /* Fix: evitar que los dropdowns de selectbox queden cortados por los containers */
    [data-testid="stVerticalBlock"] {
        overflow: visible !important;
    }
    .stSelectbox [data-baseweb="popover"] {
        z-index: 999999 !important;
    }
    .stSelectbox [role="listbox"] {
        z-index: 999999 !important;
    }
</style>
""", unsafe_allow_html=True)


# --- Variables de Estado ---
if 'blocks' not in st.session_state:
    st.session_state.blocks = [{"id": 0}]

if 'block_counter' not in st.session_state:
    st.session_state.block_counter = 1

def add_block():
    st.session_state.blocks.append({"id": st.session_state.block_counter})
    st.session_state.block_counter += 1

def remove_block(block_id):
    st.session_state.blocks = [b for b in st.session_state.blocks if b["id"] != block_id]

# --- Funciones Asíncronas para TTS ---
async def generate_tts(text, voice, output_path):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def create_audio_sync(text, voice, output_path):
    asyncio.run(generate_tts(text, voice, output_path))

# --- UI Principal ---
st.title("🎙️ Generador Bilingüe VOICER")
st.markdown("Crea inmersión bilingüe — v2.0 • 90 voces Neural • 320kbps")

st.divider()

# --- Configuración Global ---
st.subheader("⚙️ Configuración de Voces")
col1, col2 = st.columns(2)

# --- Catálogo completo de voces Neural edge-tts ---
# Español: 47 voces de 21 países — Inglés: 43 voces de 13 países
es_voices = [
    # 🇦🇷 Argentina
    "es-AR-ElenaNeural", "es-AR-TomasNeural",
    # 🇧🇴 Bolivia
    "es-BO-MarceloNeural", "es-BO-SofiaNeural",
    # 🇨🇱 Chile
    "es-CL-CatalinaNeural", "es-CL-LorenzoNeural",
    # 🇨🇴 Colombia
    "es-CO-GonzaloNeural", "es-CO-SalomeNeural",
    # 🇨🇷 Costa Rica
    "es-CR-JuanNeural", "es-CR-MariaNeural",
    # 🇨🇺 Cuba
    "es-CU-BelkysNeural", "es-CU-ManuelNeural",
    # 🇩🇴 República Dominicana
    "es-DO-EmilioNeural", "es-DO-RamonaNeural",
    # 🇪🇨 Ecuador
    "es-EC-AndreaNeural", "es-EC-LuisNeural",
    # 🇪🇸 España
    "es-ES-AlvaroNeural", "es-ES-ElviraNeural", "es-ES-XimenaNeural",
    # 🇬🇶 Guinea Ecuatorial
    "es-GQ-JavierNeural", "es-GQ-TeresaNeural",
    # 🇬🇹 Guatemala
    "es-GT-AndresNeural", "es-GT-MartaNeural",
    # 🇭🇳 Honduras
    "es-HN-CarlosNeural", "es-HN-KarlaNeural",
    # 🇲🇽 México
    "es-MX-DaliaNeural", "es-MX-JorgeNeural",
    # 🇳🇮 Nicaragua
    "es-NI-FedericoNeural", "es-NI-YolandaNeural",
    # 🇵🇦 Panamá
    "es-PA-MargaritaNeural", "es-PA-RobertoNeural",
    # 🇵🇪 Perú
    "es-PE-AlexNeural", "es-PE-CamilaNeural",
    # 🇵🇷 Puerto Rico
    "es-PR-KarinaNeural", "es-PR-VictorNeural",
    # 🇵🇾 Paraguay
    "es-PY-MarioNeural", "es-PY-TaniaNeural",
    # 🇸🇻 El Salvador
    "es-SV-LorenaNeural", "es-SV-RodrigoNeural",
    # 🇺🇸 Español (EE.UU.)
    "es-US-AlonsoNeural", "es-US-PalomaNeural",
    # 🇺🇾 Uruguay
    "es-UY-MateoNeural", "es-UY-ValentinaNeural",
    # 🇻🇪 Venezuela
    "es-VE-PaolaNeural", "es-VE-SebastianNeural",
]

en_voices = [
    # 🇦🇺 Australia
    "en-AU-NatashaNeural", "en-AU-WilliamMultilingualNeural",
    # 🇨🇦 Canadá
    "en-CA-ClaraNeural", "en-CA-LiamNeural",
    # 🇬🇧 Reino Unido
    "en-GB-LibbyNeural", "en-GB-MaisieNeural", "en-GB-RyanNeural",
    "en-GB-SoniaNeural", "en-GB-ThomasNeural",
    # 🇭🇰 Hong Kong
    "en-HK-SamNeural", "en-HK-YanNeural",
    # 🇮🇪 Irlanda
    "en-IE-ConnorNeural", "en-IE-EmilyNeural",
    # 🇮🇳 India
    "en-IN-NeerjaExpressiveNeural", "en-IN-NeerjaNeural", "en-IN-PrabhatNeural",
    # 🇰🇪 Kenia
    "en-KE-AsiliaNeural", "en-KE-ChilembaNeural",
    # 🇳🇬 Nigeria
    "en-NG-AbeoNeural", "en-NG-EzinneNeural",
    # 🇳🇿 Nueva Zelanda
    "en-NZ-MitchellNeural", "en-NZ-MollyNeural",
    # 🇵🇭 Filipinas
    "en-PH-JamesNeural", "en-PH-RosaNeural",
    # 🇸🇬 Singapur
    "en-SG-LunaNeural", "en-SG-WayneNeural",
    # 🇹🇿 Tanzania
    "en-TZ-ElimuNeural", "en-TZ-ImaniNeural",
    # 🇺🇸 Estados Unidos
    "en-US-AnaNeural", "en-US-AndrewMultilingualNeural", "en-US-AndrewNeural",
    "en-US-AriaNeural", "en-US-AvaMultilingualNeural", "en-US-AvaNeural",
    "en-US-BrianMultilingualNeural", "en-US-BrianNeural", "en-US-ChristopherNeural",
    "en-US-EmmaMultilingualNeural", "en-US-EmmaNeural", "en-US-EricNeural",
    "en-US-GuyNeural", "en-US-JennyNeural", "en-US-MichelleNeural",
    "en-US-RogerNeural", "en-US-SteffanNeural",
    # 🇿🇦 Sudáfrica
    "en-ZA-LeahNeural", "en-ZA-LukeNeural",
]

with col1:
    es_voice = st.selectbox("Voz en Español", es_voices)
with col2:
    en_voice = st.selectbox("Voz en Inglés", en_voices)

st.divider()

# --- Configuración Global ---
st.subheader("⏱️ Configuración Global")
global_pause_sec = st.slider("Pausa de Transición entre Bloques (segundos)", min_value=0.0, max_value=10.0, value=1.0, step=0.5, key="global_pause")

st.divider()

# --- Bloques Dinámicos ---
st.subheader("📝 Bloques de Frases")

# Iteramos sobre los bloques en el estado
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
            st.markdown("<br>", unsafe_allow_html=True) # Espaciado
            if st.button("❌ Eliminar", key=f"del_{b_id}"):
                remove_block(b_id)
                st.rerun()

st.button("➕ Añadir nueva frase", on_click=add_block, use_container_width=True)

st.divider()

# --- Lógica de Generación ---
if st.button("🚀 Generar Audio Final", type="primary", use_container_width=True):
    # Validar que haya al menos un bloque con texto
    has_text = any(st.session_state.get(f"es_{b['id']}") or st.session_state.get(f"en_{b['id']}") for b in st.session_state.blocks)
    
    if not has_text:
        st.warning("⚠️ Añade al menos una frase en algún bloque antes de generar.")
    else:
        with st.spinner('Generando tu pista de inmersión...'):
            final_audio = AudioSegment.empty()
            
            # Parámetros de audio consistentes — los fijamos al cargar el primer segmento
            audio_fr = 44100      # sample rate compatible con NVIDIA y edge-tts
            audio_sw = 2          # sample width en bytes (16-bit)
            audio_ch = 1          # mono
            
            # Crear directorio temporal con un string path manejado manualmente
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
                    
                    # Helper: crear silencio con los mismos parámetros que el audio real
                    def make_silence(seconds):
                        return AudioSegment.silent(
                            duration=int(seconds * 1000),
                            frame_rate=audio_fr
                        ).set_sample_width(audio_sw).set_channels(audio_ch)
                    
                    # Helper: cargar MP3 normalizando parámetros
                    def load_mp3(path):
                        seg = AudioSegment.from_mp3(path)
                        # Normalizar a los parámetros globales para evitar mismatch
                        if seg.frame_rate != audio_fr:
                            seg = seg.set_frame_rate(audio_fr)
                        if seg.sample_width != audio_sw:
                            seg = seg.set_sample_width(audio_sw)
                        if seg.channels != audio_ch:
                            seg = seg.set_channels(audio_ch)
                        return seg
                    
                    # 1. Audio en Español
                    if text_es:
                        temp_es = os.path.join(temp_dir_str, f"es_{b_id}.mp3")
                        create_audio_sync(text_es, es_voice, temp_es)
                        audio_es = load_mp3(temp_es)
                        final_audio += audio_es
                        del audio_es
                        
                        # 2. Silencio de la Tarjeta (después del español)
                        if custom_silence_sec > 0:
                            final_audio += make_silence(custom_silence_sec)
                    
                    # 3. Audio en Inglés repetido N veces
                    if text_en:
                        temp_en = os.path.join(temp_dir_str, f"en_{b_id}.mp3")
                        create_audio_sync(text_en, en_voice, temp_en)
                        audio_en = load_mp3(temp_en)
                        
                        for r in range(repetitions_en):
                            final_audio += audio_en
                            # Silencio de reflexión después de cada repetición (incluye la última)
                            if custom_silence_sec > 0:
                                final_audio += make_silence(custom_silence_sec)
                                
                        del audio_en
                    
                    # 4. Pausa de Transición Global al final del bloque
                    global_pause_val = st.session_state.get("global_pause", 1.0)
                    if global_pause_val > 0:
                        final_audio += make_silence(global_pause_val)

                st.write("Ensamblando pista final...")
                output_filename = "output_final.mp3"
                final_audio.export(output_filename, format="mp3", bitrate="320k")
            finally:
                # Limpieza manual compatible con Windows usando ignore_errors
                try:
                    shutil.rmtree(temp_dir_str, ignore_errors=True)
                except Exception as e:
                    print(f"Error limpiando directorio: {e}")
                

            
        st.success("✅ Generación completada")
        
        # --- Output: Reproductor y Descarga ---
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
