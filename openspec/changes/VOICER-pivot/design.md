# Design: VOICER Pivot

## Architecture
- **Monorepo Structure**:
  - `/frontend`: Next.js 14+ (App Router).
  - `/backend`: FastAPI Python application.

## Backend (FastAPI)
- **CORS**: Habilitado para frontend.
- **Endpoints**:
  - `GET /api/voices`: Lista en cache de las voces (ejecutando edge-tts --list-voices y filtrando "Neural").
  - `POST /api/generate`: 
    - Body: `{"blocks": [{"text": "...", "voice": "...", "rate": "+0%", "pitch": "+0Hz"}], "bg_music": "track1"}`
    - Process: edge-tts por bloque -> guardar MP3 temporal -> pydub AudioSegment -> concatenar -> overlay con ducking de bg_music -> exportar MP3.

## Frontend (Next.js)
- **State Management**: React `useState` for blocks array.
- **UI Components**: BlockList, BlockItem (Textarea, Voz, Pitch, Rate), y AudioPlayer.
- **Styling**: TailwindCSS, Soft Glassmorphism, premium aesthetic.
