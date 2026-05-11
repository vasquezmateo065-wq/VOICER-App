const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Error personalizado para respuestas de la API del backend.
 */
export class VoicerAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public endpoint?: string
  ) {
    super(message);
    this.name = "VoicerAPIError";
  }
}

/**
 * Error personalizado cuando el backend no está corriendo o es inalcanzable.
 */
export class BackendUnreachableError extends Error {
  constructor() {
    super(
      `No se pudo conectar al backend en ${API_BASE}.\n\n` +
      `🔧 Solución:\n` +
      `  1. Ejecutá "start.bat" en la raíz del proyecto, o\n` +
      `  2. Abrí una terminal en la carpeta "backend" y ejecutá:\n` +
      `     uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload`
    );
    this.name = "BackendUnreachableError";
  }
}

/**
 * Helper para fetch con manejo de errores mejorado.
 * Distingue entre errores de red (backend caído) y errores de API (backend respondió con error).
 */
async function voicerFetch(url: string, options?: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(url, options);
  } catch {
    // Error de red: backend no corre, CORS bloqueado, sin internet, etc.
    throw new BackendUnreachableError();
  }

  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // No se pudo parsear JSON, usamos el status text
    }
    throw new VoicerAPIError(detail, res.status, url);
  }

  return res;
}

export const api = {
  /** Obtener lista de voces Edge TTS (estándar) */
  voices: async () => {
    const res = await voicerFetch(`${API_BASE}/api/voices`);
    return res.json() as Promise<{
      voices: { name: string; language: string; gender: string }[];
    }>;
  },

  /** Obtener lista de voces NVIDIA (premium) */
  nvidiaVoices: async () => {
    const res = await voicerFetch(`${API_BASE}/api/nvidia/voices`);
    return res.json() as Promise<{
      voices: { name: string; language: string; gender: string; display?: string }[];
    }>;
  },

  /** Verificar si el motor NVIDIA está configurado */
  nvidiaStatus: async () => {
    const res = await voicerFetch(`${API_BASE}/api/nvidia/status`);
    return res.json() as Promise<{ configured: boolean }>;
  },

  /** Generar audio educativo bilingüe */
  generate: async (payload: {
    blocks: {
      text: string;
      text_en: string;
      voice: string;
      voice_en: string;
      rate: string;
      pitch: string;
      pause_duration: number;
      reps_en: number;
      bass: number;
      treble: number;
    }[];
    transition_pause: number;
    engine: "edge" | "nvidia";
  }) => {
    const res = await voicerFetch(`${API_BASE}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const contentType = res.headers.get("content-type") ?? "";
    if (contentType.includes("audio")) {
      return { blob: await res.blob() };
    }
    return res.json();
  },
};
