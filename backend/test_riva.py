# pyrefly: ignore [missing-import]
import riva.client
import os
# pyrefly: ignore [missing-import]
import dotenv
from riva.client.proto.riva_audio_pb2 import AudioEncoding

dotenv.load_dotenv('.env')
NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "")

auth = riva.client.Auth(
    uri="grpc.nvcf.nvidia.com:443",
    use_ssl=True,
    metadata_args=[
        ["function-id", "877104f7-e885-42b9-8de8-f6e4c6303969"],
        ["authorization", f"Bearer {NVIDIA_API_KEY}"],
    ]
)

service = riva.client.SpeechSynthesisService(auth)

results = []
def try_voice(voice_name, language_code):
    try:
        resp = service.synthesize(
            text="Hello world",
            voice_name=voice_name,
            language_code=language_code,
            sample_rate_hz=44100,
            encoding=AudioEncoding.LINEAR_PCM
        )
        results.append(f"SUCCESS: {voice_name} / {language_code}")
    except Exception as e:
        results.append(f"ERROR: {voice_name} / {language_code} -> {e}")

try_voice("Magpie-Multilingual.EN-US.Aria", "en-US")
try_voice("Magpie-Multilingual.EN-US.Sofia", "en-US")
try_voice("Magpie-Multilingual.ES-US.Aria", "es-US")

with open('riva_results3.txt', 'w', encoding='utf-8') as f:
    f.write("\n".join(results))
