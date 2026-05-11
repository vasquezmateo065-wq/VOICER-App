"use client";

import { Download, Play } from "lucide-react";

interface Props {
  url: string;
}

export default function AudioPlayer({ url }: Props) {
  const filename = `voicer_${Date.now()}.mp3`;

  return (
    <div className="glass-card glass-card-active p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full animate-pulse"
            style={{ background: "var(--accent-primary)" }} />
          <span className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
            Audio generado
          </span>
        </div>
        <a
          href={url}
          download={filename}
          className="btn-ghost text-xs">
          <Download size={13} />
          Descargar MP3
        </a>
      </div>

      <audio controls src={url} className="w-full" />

      <p className="text-xs mt-3 text-center" style={{ color: "var(--text-muted)" }}>
        Tu audio premium está listo · {filename}
      </p>
    </div>
  );
}
