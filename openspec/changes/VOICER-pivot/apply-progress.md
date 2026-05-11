# Apply Progress: VOICER Pivot

**Modo**: Standard (sin TDD)
**Estado**: Fase 2.1 completada ✅ (Frontend inicializado)

## Completed Tasks

### Phase 1: Backend Foundation (FastAPI)
- [x] 1.1 Inicializar proyecto FastAPI en `/backend`. Configurar CORS y endpoints de prueba.
- [x] 1.2 Implementar controlador de Voces (`GET /api/voices`). Ejecutar, parsear y filtrar `edge-tts` (solo Neural).
- [x] 1.3 Implementar motor de generación asíncrono. Crear endpoint `POST /api/generate` para procesar el array de bloques con `edge-tts` y concatenar con `pydub`.
- [x] 1.4 Implementar sistema de música de fondo (Audio Ducking). Superponer pista MP3 local bajando el volumen drásticamente, y exportar MP3 final.

## In Progress / Next
- Fase 2.1: Inicializar Next.js en `/frontend` con TailwindCSS. Instalar dependencias (Lucide React, framer-motion si aplica).
