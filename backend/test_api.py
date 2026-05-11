import requests
payload = {
    "blocks": [
        {
            "text": "hola",
            "text_en": "hello",
            "voice": "Magpie-Multilingual.ES-US.Mia",
            "voice_en": "Magpie-Multilingual.EN-US.Mia",
            "rate": "+0%",
            "pitch": "+0Hz",
            "pause_duration": 1,
            "reps_en": 1,
            "bass": 0,
            "treble": 0
        }
    ],
    "transition_pause": 1,
    "engine": "nvidia"
}
try:
    resp = requests.post("http://127.0.0.1:8000/api/generate", json=payload)
    print(resp.status_code)
    print(resp.text[:200])
except Exception as e:
    print(e)
