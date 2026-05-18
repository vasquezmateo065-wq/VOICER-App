"use client";

import { Music, VolumeX, Volume2 } from "lucide-react";
import { useEffect, useState } from "react";

interface Props {
  value: string | undefined;
  onChange: (v: string | undefined) => void;
  volume: number;
  onVolumeChange: (v: number) => void;
}

interface Track {
  name: string;
  filename: string;
}

export default function MusicSelector({ value, onChange, volume, onVolumeChange }: Props) {
  const [tracks, setTracks] = useState<Track[]>([]);

  useEffect(() => {
    // Música de fondo no implementada aún en el backend
    setTracks([]);
  }, []);

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <Music size={14} style={{ color: "var(--text-muted)" }} />
        <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
          Música de Fondo (opcional)
        </label>
        {value && <span className="badge badge-cyan">ON</span>}
      </div>

      <div className="grid gap-3" style={{ gridTemplateColumns: tracks.length ? "1fr 1fr" : "1fr" }}>
        <select
          id="bg-music-select"
          className="input-field"
          value={value ?? ""}
          onChange={(e) => onChange(e.target.value || undefined)}>
          <option value="">Sin música de fondo</option>
          {tracks.map((t) => (
            <option key={t.filename} value={t.name}>{t.name}</option>
          ))}
        </select>

        {value && (
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-1.5">
                <VolumeX size={12} style={{ color: "var(--text-muted)" }} />
                <span className="text-xs" style={{ color: "var(--text-muted)" }}>Vol. música</span>
                <Volume2 size={12} style={{ color: "var(--text-muted)" }} />
              </div>
              <span className="text-xs" style={{ color: "var(--accent-secondary)" }}>
                {Math.round(volume * 100)}%
              </span>
            </div>
            <input
              id="bg-music-volume"
              type="range"
              className="range-slider"
              min={0} max={0.5} step={0.05}
              value={volume}
              onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
            />
          </div>
        )}
      </div>
    </div>
  );
}
