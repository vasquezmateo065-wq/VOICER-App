export interface AudioBlock {
  id: string;
  text: string;           // Texto en español (idioma principal)
  textEn: string;         // Texto en inglés (traducción/repetición)
  voice: string;          // Voz neural para español (SIEMPRE edge-tts)
  voiceEn: string;        // Voz neural para inglés (NVIDIA o edge-tts según motor)
  rate: number;           // -50 to +100 (%)
  pitch: number;          // -20 to +20 (Hz)
  pauseDuration: number;  // Segundos de pausa entre español e inglés (0-10)
  repsEn: number;         // Repeticiones del audio en inglés (1-5)
  bass: number;           // Cuerpo / Graves: -10 to +10 (dB)
  treble: number;         // Claridad / Agudos: -10 to +10 (dB)
}

export interface Voice {
  name: string;
  language: string;
  gender: string;
  display?: string;  // Nombre amigable (NVIDIA voices)
}

export interface GenerateRequest {
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
}

export interface GenerateResponse {
  status: string;
  message: string;
  audio_path: string;
  blocks_processed: number;
}
