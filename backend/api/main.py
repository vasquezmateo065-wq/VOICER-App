# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import FileResponse
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import asyncio
import httpx
import subprocess
import tempfile
import shutil
import os
import time as time_module
from pathlib import Path
from pydub import AudioSegment
import shutil as _shutil


def _get_ffmpeg() -> str:
    """Devuelve la ruta a ffmpeg, descargándolo con imageio-ffmpeg si es necesario."""
    ffmpeg = _shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg
    import imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()

# Cargar variables de entorno desde backend/.env
load_dotenv(Path(__file__).parent.parent / ".env")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "")

# Directorio donde se guardan los audios generados
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="VOICER API",
    description="API para generación de audio educativo bilingüe con motor dual (Edge-TTS + NVIDIA)",
    version="4.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================================================================
# HEALTH
# ===========================================================================

@app.get("/api/health")
async def health_check():
    nvidia_configured = bool(NVIDIA_API_KEY and NVIDIA_API_KEY != "your_nvidia_api_key_here")
    return {
        "status": "ok",
        "message": "VOICER API is running",
        "engines": {
            "edge_tts": True,
            "nvidia": nvidia_configured,
        }
    }


# ===========================================================================
# VOICES — EDGE-TTS
# ===========================================================================

EDGE_VOICES_CACHE: list = []


async def fetch_neural_voices() -> list:
    try:
        process = await asyncio.create_subprocess_exec(
            "edge-tts", "--list-voices",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"Error from edge-tts: {stderr.decode()}")
            return []

        voices = []
        for line in stdout.decode().splitlines():
            if "Neural" in line:
                parts = line.split()
                if not parts:
                    continue
                name = parts[0]
                name_parts = name.split("-")
                language = "-".join(name_parts[:2]) if len(name_parts) >= 2 else "Unknown"
                gender = parts[1] if len(parts) > 1 else "Unknown"
                voices.append({"name": name, "language": language, "gender": gender})

        return voices
    except Exception as e:
        print(f"Error fetching voices: {e}")
        return []


@app.on_event("startup")
async def startup_event():
    global EDGE_VOICES_CACHE
    print("Cargando voces desde edge-tts...")
    EDGE_VOICES_CACHE = await fetch_neural_voices()
    print(f"Se cargaron {len(EDGE_VOICES_CACHE)} voces Neural.")
    if NVIDIA_API_KEY and NVIDIA_API_KEY != "your_nvidia_api_key_here":
        print("[OK] Motor NVIDIA configurado.")
    else:
        print("[!] NVIDIA_API_KEY no configurada -- motor Premium desactivado.")


@app.get("/api/voices")
async def get_voices():
    global EDGE_VOICES_CACHE
    if not EDGE_VOICES_CACHE:
        EDGE_VOICES_CACHE = await fetch_neural_voices()
    return {"voices": EDGE_VOICES_CACHE}


# ===========================================================================
# VOICES — NVIDIA
# ===========================================================================

# Voces NVIDIA Riva TTS — Catálogo oficial según ficha técnica
# Modelo: Magpie-Multilingual (function-id: 877104f7-e885-42b9-8de8-f6e4c6303969)
# Language: en-US (Inglés EE.UU.)
# Emociones disponibles: Default, Angry, Calm, Happy, Neutral, Sad
# Formato: Magpie-Multilingual.EN-US.{Speaker}
NVIDIA_VOICES = [
    # ── Voces Femeninas (en-US) ──
    {"name": "Magpie-Multilingual.EN-US.Mia",      "language": "en-US", "gender": "Female", "display": "🎤 Mia (F)"},
    {"name": "Magpie-Multilingual.EN-US.Sofia",    "language": "en-US", "gender": "Female", "display": "🎤 Sofia (F)"},
    {"name": "Magpie-Multilingual.EN-US.Aria",     "language": "en-US", "gender": "Female", "display": "🎤 Aria (F)"},
    {"name": "Magpie-Multilingual.EN-US.Isabela",  "language": "en-US", "gender": "Female", "display": "🎤 Isabela (F)"},
    {"name": "Magpie-Multilingual.EN-US.Louise",   "language": "en-US", "gender": "Female", "display": "🎤 Louise (F)"},

    # ── Voces Masculinas (en-US) ──
    {"name": "Magpie-Multilingual.EN-US.Diego",    "language": "en-US", "gender": "Male",   "display": "🎙️ Diego (M)"},
    {"name": "Magpie-Multilingual.EN-US.Pascal",   "language": "en-US", "gender": "Male",   "display": "🎙️ Pascal (M)"},
    {"name": "Magpie-Multilingual.EN-US.Jason",    "language": "en-US", "gender": "Male",   "display": "🎙️ Jason (M)"},
    {"name": "Magpie-Multilingual.EN-US.Leo",      "language": "en-US", "gender": "Male",   "display": "🎙️ Leo (M)"},
    {"name": "Magpie-Multilingual.EN-US.Ray",      "language": "en-US", "gender": "Male",   "display": "🎙️ Ray (M)"},

]

# Emociones disponibles para el selector de la UI
NVIDIA_EMOTIONS = ["Default", "Angry", "Calm", "Happy", "Neutral", "Sad"]


@app.get("/api/nvidia/voices")
async def get_nvidia_voices():
    """Devuelve la lista de voces disponibles en el motor NVIDIA."""
    if not NVIDIA_API_KEY or NVIDIA_API_KEY == "your_nvidia_api_key_here":
        raise HTTPException(
            status_code=503,
            detail="Motor NVIDIA no configurado. Agregá tu NVIDIA_API_KEY en backend/.env"
        )
    return {"voices": NVIDIA_VOICES, "emotions": NVIDIA_EMOTIONS}


@app.get("/api/nvidia/status")
async def nvidia_status():
    """Verifica si el motor NVIDIA está configurado."""
    configured = bool(NVIDIA_API_KEY and NVIDIA_API_KEY != "your_nvidia_api_key_here")
    return {"configured": configured}


# ===========================================================================
# AUDIO GENERATION — MODELS
# ===========================================================================

class LearningCard(BaseModel):
    """Tarjeta de aprendizaje: español + inglés con pausa y repeticiones."""
    text: str = Field(..., min_length=1, description="Texto en español")
    text_en: str = Field(default="", description="Texto en inglés (traducción)")
    voice: str = Field(..., description="Voz para español — siempre edge-tts (ej: es-AR-ElenaNeural)")
    voice_en: str = Field(default="Magpie-Multilingual.EN-US.Sofia", description="Voz en inglés (NVIDIA: Magpie-Multilingual.EN-US.Sofia, Edge: en-US-JennyNeural)")
    rate: str = Field(default="+0%", description="Velocidad — solo para motor Edge")
    pitch: str = Field(default="+0Hz", description="Tono — solo para motor Edge")
    pause_duration: float = Field(default=3.0, ge=0.0, le=10.0)
    reps_en: int = Field(default=2, ge=1, le=5)
    bass: int = Field(default=0, ge=-10, le=10, description="Graves EQ en dB")
    treble: int = Field(default=0, ge=-10, le=10, description="Agudos EQ en dB")
    emotion: str = Field(default="Default", description="Emoción NVIDIA: Default, Angry, Calm, Happy, Neutral, Sad")


class GenerateRequest(BaseModel):
    blocks: list[LearningCard] = Field(..., min_length=1)
    transition_pause: float = Field(default=3.0, ge=0.0, le=10.0)
    engine: str = Field(default="edge", description="Motor de síntesis: 'edge' o 'nvidia'")


# ===========================================================================
# TTS ENGINES
# ===========================================================================

def parse_rate(rate_str: str) -> str:
    if not rate_str:
        return "+0%"
    rate_str = rate_str.strip()
    if rate_str.endswith('%'):
        return rate_str
    return "+0%"


def parse_pitch(pitch_str: str) -> str:
    if not pitch_str:
        return "+0Hz"
    pitch_str = pitch_str.strip()
    if pitch_str.endswith('Hz'):
        return pitch_str
    return "+0Hz"


async def generate_edge_audio(text: str, voice: str, rate: str, pitch: str, out_path: str) -> bool:
    """Genera audio usando edge-tts (motor Estándar)."""
    rate = parse_rate(rate)
    pitch = parse_pitch(pitch)
    
    # Ajuste sutil para naturalidad: -5% evita compresión/artificialidad en voces neurales
    if rate == "+0%":
        rate = "-5%"

    cmd = [
        "edge-tts",
        "--voice", voice,
        "--text", text,
        f"--rate={rate}",
        f"--pitch={pitch}",
        "--write-media", out_path
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"Error edge-tts: {stderr.decode()}")
            return False

        return os.path.exists(out_path)
    except Exception as e:
        print(f"Excepción edge-tts: {e}")
        return False


async def generate_nvidia_audio(text: str, voice: str, out_path: str) -> bool:
    """Genera audio con NVIDIA Magpie TTS usando el cliente oficial gRPC."""
    if not NVIDIA_API_KEY or NVIDIA_API_KEY == "your_nvidia_api_key_here":
        print("NVIDIA_API_KEY no configurada")
        return False

    import riva.client
    from riva.client.proto.riva_audio_pb2 import AudioEncoding
    import asyncio
    import wave
    import subprocess
    import os

    # Sanitización de variables residuales (ej: un cliente mandó un payload viejo de UI en caché)
    # Reemplazamos viejos modelos o prefijos erróneos que puedan causar el error "language es-ES not found"
    if "ES-ES" in voice.upper() or "es-es" in voice.lower():
        voice = voice.replace("ES-ES", "ES-US").replace("es-ES", "ES-US").replace("es-es", "ES-US")

    # Mapear nombres obsoletos o mal escritos a sus equivalentes correctos
    obsolete_mappings = {
        # Nombres con errores de tipeo o variantes antiguas
        "Magpie-Multilingual.EN-US.Isabella": "Magpie-Multilingual.EN-US.Isabela",
        # Voces no disponibles en este despliegue — redirigidas a alternativas similares
        "Magpie-Multilingual.EN-US.Emma":   "Magpie-Multilingual.EN-US.Sofia",
        "Magpie-Multilingual.EN-US.Brian":  "Magpie-Multilingual.EN-US.Jason",
        # Formato antiguo Riva gRPC (pre-Magpie)
        "English-US.Female-1": "Magpie-Multilingual.EN-US.Mia",
        "English-US.Female-2": "Magpie-Multilingual.EN-US.Sofia",
        "English-US.Female-3": "Magpie-Multilingual.EN-US.Aria",
        "English-US.Female-4": "Magpie-Multilingual.EN-US.Isabela",
        "English-US.Female-5": "Magpie-Multilingual.EN-US.Louise",
        "English-US.Male-1":   "Magpie-Multilingual.EN-US.Diego",
        "English-US.Male-2":   "Magpie-Multilingual.EN-US.Pascal",
        "English-US.Male-3":   "Magpie-Multilingual.EN-US.Jason",
        "English-US.Male-4":   "Magpie-Multilingual.EN-US.Leo",
        # Formato español antiguo — redirigido a edge-tts (ya no se usa NVIDIA para ES)
        "Spanish-ES.Female-1": "Magpie-Multilingual.EN-US.Mia",
        "Spanish-US.Female-1": "Magpie-Multilingual.EN-US.Mia",
        # ES-US antiguo
        "Magpie-Multilingual.ES-US.Sofia":    "Magpie-Multilingual.EN-US.Sofia",
        "Magpie-Multilingual.ES-US.Aria":     "Magpie-Multilingual.EN-US.Aria",
        "Magpie-Multilingual.ES-US.Mia":      "Magpie-Multilingual.EN-US.Mia",
        "Magpie-Multilingual.ES-US.Isabela":  "Magpie-Multilingual.EN-US.Isabela",
        "Magpie-Multilingual.ES-US.Louise":   "Magpie-Multilingual.EN-US.Louise",
        "Magpie-Multilingual.ES-US.Diego":    "Magpie-Multilingual.EN-US.Diego",
        "Magpie-Multilingual.ES-US.Pascal":   "Magpie-Multilingual.EN-US.Pascal",
        "Magpie-Multilingual.ES-US.Jason":    "Magpie-Multilingual.EN-US.Jason",
        "Magpie-Multilingual.ES-US.Leo":      "Magpie-Multilingual.EN-US.Leo",
    }
    if voice in obsolete_mappings:
        voice = obsolete_mappings[voice]

    # Parsear voice_name de Magpie TTS: "Magpie-Multilingual.ES-US.Sofia" → lang_code="es-US"
    # El voice_name se pasa completo a Riva (incluye prefijo de idioma)
    parts = voice.split(".")
    if len(parts) >= 2:
        # El segundo segmento suele ser el locale (ES-US, EN-US, etc.)
        raw_lang = parts[1]
        lang_parts = raw_lang.split("-")
        if len(lang_parts) == 2:
            lang_code = f"{lang_parts[0].lower()}-{lang_parts[1].upper()}"
        else:
            lang_code = "en-US"
    else:
        lang_code = "en-US"
    
    # Prevenir que lang_code llegue a es-ES bajo cualquier circunstancia
    if lang_code == "es-ES":
        lang_code = "es-US"
        
    voice_name = voice  # Nombre completo: "Magpie-Multilingual.ES-US.Sofia"

    def _sync_generate():
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
                voice_name=voice_name,
                language_code=lang_code,
                sample_rate_hz=44100,
                encoding=AudioEncoding.LINEAR_PCM
            )
            
            # Guardar el WAV temporal
            wav_path = out_path.replace(".mp3", ".wav")
            with wave.open(wav_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframesraw(resp.audio)
            
            # Convertir WAV a MP3 usando FFmpeg (auto-descargado si no está en el sistema)
            result = subprocess.run(
                [_get_ffmpeg(), "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-q:a", "2", out_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            # Limpiar WAV temporal
            try:
                os.remove(wav_path)
            except Exception:
                pass
                
            return result.returncode == 0 and os.path.exists(out_path)
        except Exception as e:
            # Propagar el error exacto para debugging visual
            error_msg = str(e)
            print(f"Riva gRPC Error: {error_msg}")
            raise HTTPException(status_code=500, detail=f"NVIDIA gRPC API Error: {error_msg}")
            
    # Ejecutar la operación sincrónica de gRPC en un thread para no bloquear asyncio
    return await asyncio.to_thread(_sync_generate)


async def generate_tts_audio(
    text: str, voice: str, rate: str, pitch: str, out_path: str, engine: str
) -> bool:
    """
    Dispatcher: elige el motor correcto según `engine`.
    - "nvidia" → NVIDIA Magpie TTS (solo para inglés)
    - "edge"   → edge-tts (español e inglés estándar)
    """
    if engine == "nvidia":
        return await generate_nvidia_audio(text, voice, out_path)
    else:
        return await generate_edge_audio(text, voice, rate, pitch, out_path)


# ===========================================================================
# EQ POST-PROCESSING
# ===========================================================================

def apply_eq_ffmpeg(input_path: str, output_path: str, bass: int, treble: int) -> bool:
    """
    Aplica ecualización de graves y agudos usando FFmpeg.
    No-op si ambos son 0 (evita procesamiento innecesario).
    """
    if bass == 0 and treble == 0:
        if input_path != output_path:
            shutil.copy2(input_path, output_path)
        return True

    filters = []
    if bass != 0:
        filters.append(f"bass=g={bass}:f=100:w=0.5")
    if treble != 0:
        filters.append(f"treble=g={treble}:f=3000:w=0.5")

    cmd = [
        _get_ffmpeg(), "-y",
        "-i", input_path,
        "-af", ",".join(filters),
        "-codec:a", "libmp3lame",
        "-q:a", "2",
        output_path
    ]

    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
        if result.returncode != 0:
            print(f"FFmpeg EQ error: {result.stderr.decode()[-300:]}")
            return False
        return True
    except Exception as e:
        print(f"FFmpeg EQ excepción: {e}")
        return False


# ===========================================================================
# CARD ASSEMBLER
# ===========================================================================

# Audio quality constants — evitar distorsión por mismatch de sample rate
AUDIO_FR = 44100      # sample rate (NVIDIA nativo 44.1kHz, edge-tts se upsampling limpio)
AUDIO_SW = 2          # sample width en bytes (16-bit)
AUDIO_CH = 1          # mono


def _make_silence(duration_ms: int) -> AudioSegment:
    """Crea silencio con parámetros de alta calidad consistentes con el audio TTS."""
    return AudioSegment.silent(
        duration=duration_ms,
        frame_rate=AUDIO_FR
    ).set_sample_width(AUDIO_SW).set_channels(AUDIO_CH)


def _load_mp3_normalized(path: str) -> AudioSegment:
    """Carga MP3 normalizando sample rate, width y canales para evitar artifacts."""
    seg = AudioSegment.from_mp3(path)
    if seg.frame_rate != AUDIO_FR:
        seg = seg.set_frame_rate(AUDIO_FR)
    if seg.sample_width != AUDIO_SW:
        seg = seg.set_sample_width(AUDIO_SW)
    if seg.channels != AUDIO_CH:
        seg = seg.set_channels(AUDIO_CH)
    # Fade in/out sutil — suaviza artefactos del modelo NVIDIA en bordes de frases
    if len(seg) > 60:
        seg = seg.fade_in(10).fade_out(30)
    return seg


async def assemble_learning_card(
    card: LearningCard, temp_dir: str, card_index: int, engine: str
) -> AudioSegment:
    """
    Ensambla una tarjeta completa con arquitectura HÍBRIDA:
    - Español → SIEMPRE edge-tts (suena excelente, sin excepción)
    - Inglés  → motor seleccionado (edge o nvidia)
    
    Secuencia: [ES_EQ] + [Pausa] + ([EN_EQ] + [Pausa]) × reps_en
    """
    # 1. TTS Español — FUERZA edge-tts siempre, incluso en modo Premium
    # Sanitización: si la voz española es formato NVIDIA, usar default edge-tts
    es_voice = card.voice
    if es_voice.startswith("Magpie-Multilingual") or es_voice.startswith("English-") or es_voice.startswith("Spanish-"):
        es_voice = "es-AR-ElenaNeural"
    
    es_raw = os.path.join(temp_dir, f"card_{card_index}_es_raw.mp3")
    ok = await generate_edge_audio(card.text, es_voice, card.rate, card.pitch, es_raw)
    if not ok:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando voz español (tarjeta {card_index + 1})"
        )

    # 2. EQ Español
    es_eq = os.path.join(temp_dir, f"card_{card_index}_es_eq.mp3")
    if not apply_eq_ffmpeg(es_raw, es_eq, card.bass, card.treble):
        es_eq = es_raw

    es_audio = _load_mp3_normalized(es_eq)

    # Solo español si no hay texto en inglés
    if not card.text_en.strip():
        return es_audio

    # 3. Silencio de reflexión (alta calidad)
    pause_ms = int(card.pause_duration * 1000)
    silence = _make_silence(pause_ms) if pause_ms > 0 else AudioSegment.empty()

    # 4. TTS Inglés — usa el motor seleccionado (edge o nvidia)
    en_raw = os.path.join(temp_dir, f"card_{card_index}_en_raw.mp3")
    ok = await generate_tts_audio(card.text_en, card.voice_en, card.rate, card.pitch, en_raw, engine)
    if not ok:
        raise HTTPException(
            status_code=500,
            detail=f"Error generando voz inglés (tarjeta {card_index + 1})"
        )

    # 5. EQ Inglés
    en_eq = os.path.join(temp_dir, f"card_{card_index}_en_eq.mp3")
    if not apply_eq_ffmpeg(en_raw, en_eq, card.bass, card.treble):
        en_eq = en_raw

    en_audio = _load_mp3_normalized(en_eq)

    # 6. Ensamblado: [ES] + [Pausa] + ([EN] + [Pausa]) × N
    result = es_audio + silence
    for rep in range(card.reps_en):
        result += en_audio
        if rep < card.reps_en - 1:
            result += silence

    return result


# ===========================================================================
# GENERATE ENDPOINT
# ===========================================================================

@app.post("/api/generate")
async def generate_audio(request: GenerateRequest):
    """
    Genera audio educativo bilingüe.
    
    Parámetro `engine`:
    - "edge"   → edge-tts (gratis, rápido, 322+ voces Neural)
    - "nvidia" → NVIDIA magpie-tts-multilingual (IA generativa, máxima calidad)
    
    Secuencia por tarjeta: [ES] + [Pausa] + ([EN] + [Pausa]) × reps_en
    """
    if not request.blocks:
        raise HTTPException(status_code=400, detail="Debe proporcionar al menos una tarjeta")

    engine = request.engine.lower()
    if engine not in ("edge", "nvidia"):
        raise HTTPException(status_code=400, detail="engine debe ser 'edge' o 'nvidia'")

    if engine == "nvidia" and (not NVIDIA_API_KEY or NVIDIA_API_KEY == "your_nvidia_api_key_here"):
        raise HTTPException(
            status_code=503,
            detail="Motor NVIDIA no configurado. Agregá tu NVIDIA_API_KEY en backend/.env"
        )

    temp_dir = tempfile.mkdtemp(prefix="voicer_")

    try:
        combined = AudioSegment.empty()

        transition_ms = int(request.transition_pause * 1000)
        card_transition = (
            _make_silence(transition_ms)
            if transition_ms > 0
            else AudioSegment.empty()
        )

        for i, card in enumerate(request.blocks):
            card_audio = await assemble_learning_card(card, temp_dir, i, engine)
            if i > 0:
                combined += card_transition
            combined += card_audio

        output_filename = f"voicer_{int(time_module.time())}.mp3"
        final_path = OUTPUT_DIR / output_filename
        combined.export(str(final_path), format="mp3", bitrate="320k")

        return FileResponse(
            path=str(final_path),
            media_type="audio/mpeg",
            filename=output_filename,
            headers={
                "X-Blocks-Processed": str(len(request.blocks)),
                "X-Engine": engine,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
