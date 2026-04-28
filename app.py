import streamlit as st
import asyncio
import edge_tts
from pydub import AudioSegment
import tempfile
import os
import shutil

# --- Configuración de la página ---
st.set_page_config(page_title="VOICER", page_icon="🎙️", layout="centered")

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
st.markdown("Crea inmersión bilingüe en audio mediante bloques personalizables.")

st.divider()

# --- Configuración Global ---
st.subheader("⚙️ Configuración de Voces")
col1, col2 = st.columns(2)

# Listas reducidas de voces populares
es_voices = [
    "es-MX-JorgeNeural", "es-MX-DaliaNeural", 
    "es-ES-AlvaroNeural", "es-ES-ElviraNeural",
    "es-CO-GonzaloNeural", "es-AR-TomasNeural"
]
en_voices = [
    "en-US-GuyNeural", "en-US-AriaNeural", 
    "en-GB-SoniaNeural", "en-GB-RyanNeural",
    "en-AU-NatashaNeural"
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
                    
                    # 1. Audio en Español
                    if text_es:
                        temp_es = os.path.join(temp_dir_str, f"es_{b_id}.mp3")
                        create_audio_sync(text_es, es_voice, temp_es)
                        # Forzar liberación de handle en Windows usando with open
                        with open(temp_es, "rb") as f:
                            audio_es = AudioSegment.from_file(f, format="mp3")
                        final_audio += audio_es
                        del audio_es
                        
                        # 2. Silencio de la Tarjeta (después del español)
                        if custom_silence_sec > 0:
                            custom_silence = AudioSegment.silent(duration=int(custom_silence_sec * 1000))
                            final_audio += custom_silence
                    
                    # 3. Audio en Inglés repetido N veces
                    if text_en:
                        temp_en = os.path.join(temp_dir_str, f"en_{b_id}.mp3")
                        create_audio_sync(text_en, en_voice, temp_en)
                        # Forzar liberación de handle en Windows usando with open
                        with open(temp_en, "rb") as f:
                            audio_en = AudioSegment.from_file(f, format="mp3")
                        
                        for r in range(repetitions_en):
                            final_audio += audio_en
                            # Silencio de la Tarjeta entre repeticiones y al final
                            if custom_silence_sec > 0:
                                custom_silence = AudioSegment.silent(duration=int(custom_silence_sec * 1000))
                                final_audio += custom_silence
                                
                        del audio_en
                    
                    # 4. Pausa de Transición Global al final del bloque
                    global_pause_val = st.session_state.get("global_pause", 1.0)
                    if global_pause_val > 0:
                        final_audio += AudioSegment.silent(duration=int(global_pause_val * 1000))

                st.write("Ensamblando pista final...")
                output_filename = "output_final.mp3"
                final_audio.export(output_filename, format="mp3")
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
