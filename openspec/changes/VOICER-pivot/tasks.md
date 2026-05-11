# Tasks: VOICER Pivot

## Phase 1: Backend Foundation (FastAPI)
- [x] 1.1 Inicializar proyecto FastAPI en `/backend`. Configurar CORS y endpoints de prueba.
- [x] 1.2 Implementar controlador de Voces (`GET /api/voices`). Ejecutar, parsear y filtrar `edge-tts` (solo Neural).
- [ ] 1.3 Implementar motor de generación asíncrono. Crear endpoint `POST /api/generate` para recibir el array de bloques (`text`, `voice`, `rate`, `pitch`), generar los audios individuales con `edge-tts` y concatenarlos usando `pydub`.
- [x] 1.4 Implementar sistema de música de fondo (Audio Ducking). Superponer pista MP3 local bajando el volumen drásticamente, y exportar MP3 final.

## Phase 2: Frontend Foundation (Next.js)
- [ ] 2.1 Inicializar Next.js en `/frontend` con TailwindCSS. Instalar dependencias (Lucide React, framer-motion si aplica).
- [ ] 2.2 Diseñar el Layout principal (UI Premium, Dark Mode, sidebar o dashboard limpio).
- [ ] 2.3 Crear estado global o local para gestionar la lista de Bloques (Añadir, eliminar, reordenar).

## Phase 3: Frontend Components & Integration
- [ ] 3.1 Crear componente `AudioBlock`: Input de texto, select de voces (consumiendo la API), y sliders de Rate/Pitch.
- [ ] 3.2 Crear Panel de Control Global: Selector de música de fondo y botón "Generar Audio".
- [ ] 3.3 Integrar `POST /api/generate`, manejar estado de carga (loading spinner), y mostrar reproductor de audio final para escuchar/descargar.
