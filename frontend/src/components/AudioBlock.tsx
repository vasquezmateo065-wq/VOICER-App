"use client";

import { useId, useMemo, useState } from "react";
import { AudioBlock as AudioBlockType, Voice } from "@/types";
import { ChevronUp, ChevronDown, Copy, Trash2, Mic, Globe, Clock, Repeat, SlidersHorizontal, ChevronDown as ChevronDownSmall } from "lucide-react";

interface Props {
  block: AudioBlockType;
  index: number;
  total: number;
  voices: Voice[];          // Voces para inglés (según motor seleccionado)
  edgeVoices: Voice[];      // Voces edge-tts (SIEMPRE para español)
  voicesLoading: boolean;
  engine: "edge" | "nvidia";
  onUpdate: (patch: Partial<AudioBlockType>) => void;
  onRemove: () => void;
  onDuplicate: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
}

// Friendly country names for language codes
const COUNTRY_NAMES: Record<string, string> = {
  "es-AR": "🇦🇷 Argentina",
  "es-BO": "🇧🇴 Bolivia",
  "es-CL": "🇨🇱 Chile",
  "es-CO": "🇨🇴 Colombia",
  "es-CR": "🇨🇷 Costa Rica",
  "es-CU": "🇨🇺 Cuba",
  "es-DO": "🇩🇴 Rep. Dominicana",
  "es-EC": "🇪🇨 Ecuador",
  "es-SV": "🇸🇻 El Salvador",
  "es-GQ": "🇬🇶 Guinea Ecuatorial",
  "es-GT": "🇬🇹 Guatemala",
  "es-HN": "🇭🇳 Honduras",
  "es-MX": "🇲🇽 México",
  "es-NI": "🇳🇮 Nicaragua",
  "es-PA": "🇵🇦 Panamá",
  "es-PY": "🇵🇾 Paraguay",
  "es-PE": "🇵🇪 Perú",
  "es-PR": "🇵🇷 Puerto Rico",
  "es-ES": "🇪🇸 España",
  "es-US": "🇺🇸 US Spanish",
  "es-UY": "🇺🇾 Uruguay",
  "es-VE": "🇻🇪 Venezuela",
  "en-AU": "🇦🇺 Australia",
  "en-CA": "🇨🇦 Canada",
  "en-GH": "🇬🇭 Ghana",
  "en-HK": "🇭🇰 Hong Kong",
  "en-IN": "🇮🇳 India",
  "en-IE": "🇮🇪 Ireland",
  "en-KE": "🇰🇪 Kenya",
  "en-NZ": "🇳🇿 New Zealand",
  "en-NG": "🇳🇬 Nigeria",
  "en-PH": "🇵🇭 Philippines",
  "en-SG": "🇸🇬 Singapore",
  "en-ZA": "🇿🇦 South Africa",
  "en-TZ": "🇹🇿 Tanzania",
  "en-GB": "🇬🇧 UK",
  "en-US": "🇺🇸 US",
};

function getCountryName(langCode: string): string {
  return COUNTRY_NAMES[langCode] ?? langCode;
}

// Extract display name — uses voice.display if available (NVIDIA), otherwise parses Edge format
function getVoiceDisplayName(voice: { name: string; gender: string; display?: string }): string {
  if (voice.display) return voice.display;
  // Edge format: "es-AR-ElenaNeural" → "Elena (F)"
  const parts = voice.name.split("-");
  const raw = parts.slice(2).join("-").replace("Neural", "");
  return `${raw} (${voice.gender[0]})`;
}

// Get the country/region code from a voice name
// Edge: "es-AR-ElenaNeural" → "es-AR"
// NVIDIA: "Spanish-ES.Female-1" → language field is "es-ES"
function getVoiceCountry(voice: string, allVoices: { name: string; language: string }[]): string {
  // First try to find it in the voices list (most reliable for NVIDIA)
  const found = allVoices.find((v) => v.name === voice);
  if (found) return found.language;
  // Fallback: Edge format split
  const parts = voice.split("-");
  return parts.length >= 2 ? `${parts[0]}-${parts[1]}` : voice;
}

interface VoiceSelectorProps {
  uid: string;
  label: string;
  langPrefix: string;
  voices: Voice[];
  loading: boolean;
  selectedVoice: string;
  onVoiceChange: (voice: string) => void;
  accentColor: string;
}

function VoiceSelector({ uid, label, langPrefix, voices, loading, selectedVoice, onVoiceChange, accentColor }: VoiceSelectorProps) {
  // Filter voices by language prefix
  const langVoices = useMemo(
    () => voices.filter((v) => v.language.startsWith(langPrefix)),
    [voices, langPrefix]
  );

  // Get unique countries sorted
  const countries = useMemo(() => {
    const set = new Set(langVoices.map((v) => v.language));
    return Array.from(set).sort((a, b) => getCountryName(a).localeCompare(getCountryName(b)));
  }, [langVoices]);

  // Current selected country — use all voices to resolve NVIDIA format
  let selectedCountry = getVoiceCountry(selectedVoice, voices);
  
  // Safety fallback: if the country isn't in our list (e.g. switched engines), use the first available
  if (countries.length > 0 && !countries.includes(selectedCountry)) {
    selectedCountry = countries[0];
  }

  // Voices for the selected country
  const countryVoices = useMemo(
    () => langVoices.filter((v) => v.language === selectedCountry),
    [langVoices, selectedCountry]
  );

  // When changing country, auto-select the first voice of that country
  const handleCountryChange = (country: string) => {
    const firstVoice = langVoices.find((v) => v.language === country);
    if (firstVoice) onVoiceChange(firstVoice.name);
  };

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-2">
        <select className="input-field" disabled><option>Cargando…</option></select>
        <select className="input-field" disabled><option>—</option></select>
      </div>
    );
  }

  return (
    <div>
      <label className="block text-xs font-medium mb-1" style={{ color: "var(--text-muted)" }}>
        {label}
      </label>
      <div className="grid grid-cols-2 gap-2">
        {/* Country selector */}
        <select
          id={`${uid}-country`}
          className="input-field"
          value={selectedCountry}
          onChange={(e) => handleCountryChange(e.target.value)}
          style={{ borderColor: accentColor + "33" }}
        >
          {countries.map((c) => (
            <option key={c} value={c}>{getCountryName(c)}</option>
          ))}
        </select>

        {/* Voice selector (filtered by country) */}
        <select
          id={`${uid}-voice`}
          className="input-field"
          value={selectedVoice}
          onChange={(e) => onVoiceChange(e.target.value)}
          style={{ borderColor: accentColor + "33" }}
        >
          {countryVoices.map((v) => (
            <option key={v.name} value={v.name}>
              {getVoiceDisplayName(v)}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

interface EQSectionProps {
  uid: string;
  block: AudioBlockType;
  onUpdate: (patch: Partial<AudioBlockType>) => void;
}

function EQSection({ uid, block, onUpdate }: EQSectionProps) {
  const isActive = block.bass !== 0 || block.treble !== 0;
  const [open, setOpen] = useState(isActive);

  return (
    <div className="mt-3">
      {/* Toggle header */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 w-full text-left py-1.5"
        style={{ color: "var(--text-muted)" }}
      >
        <SlidersHorizontal size={12} />
        <span className="text-xs font-medium">Modulación de Voz</span>
        {isActive && (
          <span className="text-xs px-1.5 py-0.5 rounded font-semibold"
            style={{ background: "var(--accent-soft)", color: "var(--accent-primary)", fontSize: "10px" }}>
            EQ
          </span>
        )}
        <ChevronDownSmall
          size={12}
          style={{
            marginLeft: "auto",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.2s",
          }}
        />
      </button>

      {/* EQ sliders */}
      {open && (
        <div className="grid grid-cols-2 gap-3 mt-2 pt-3"
          style={{ borderTop: "1px solid var(--border-subtle)" }}>
          {/* Bass */}
          <div>
            <label className="flex justify-between text-xs font-medium mb-1">
              <span style={{ color: "var(--text-muted)" }}>Cuerpo (Graves)</span>
              <span style={{
                color: block.bass === 0 ? "var(--text-muted)" : block.bass > 0 ? "#a78bfa" : "#60a5fa",
                fontVariantNumeric: "tabular-nums",
              }}>
                {block.bass >= 0 ? "+" : ""}{block.bass}dB
              </span>
            </label>
            <input
              id={`block-bass-${uid}`}
              type="range"
              className="range-slider"
              min={-10} max={10} step={1}
              value={block.bass}
              onChange={(e) => onUpdate({ bass: parseInt(e.target.value) })}
            />
            <div className="flex justify-between text-xs mt-0.5" style={{ color: "var(--text-muted)", opacity: 0.5 }}>
              <span>Seco</span><span>Cálido</span>
            </div>
          </div>

          {/* Treble */}
          <div>
            <label className="flex justify-between text-xs font-medium mb-1">
              <span style={{ color: "var(--text-muted)" }}>Claridad (Agudos)</span>
              <span style={{
                color: block.treble === 0 ? "var(--text-muted)" : block.treble > 0 ? "#34d399" : "#f87171",
                fontVariantNumeric: "tabular-nums",
              }}>
                {block.treble >= 0 ? "+" : ""}{block.treble}dB
              </span>
            </label>
            <input
              id={`block-treble-${uid}`}
              type="range"
              className="range-slider"
              min={-10} max={10} step={1}
              value={block.treble}
              onChange={(e) => onUpdate({ treble: parseInt(e.target.value) })}
            />
            <div className="flex justify-between text-xs mt-0.5" style={{ color: "var(--text-muted)", opacity: 0.5 }}>
              <span>Suave</span><span>Nítido</span>
            </div>
          </div>

          {/* Reset */}
          {isActive && (
            <button
              type="button"
              className="col-span-2 text-xs text-center py-1 rounded"
              style={{ color: "var(--text-muted)", background: "rgba(255,255,255,0.04)" }}
              onClick={() => onUpdate({ bass: 0, treble: 0 })}
            >
              Restablecer EQ
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function AudioBlock({
  block, index, total, voices, edgeVoices, voicesLoading, engine,
  onUpdate, onRemove, onDuplicate, onMoveUp, onMoveDown,
}: Props) {
  const uid = useId();
  const hasText = block.text.trim().length > 0;
  const hasEnglish = block.textEn.trim().length > 0;

  return (
    <div className={`glass-card p-5 ${hasText ? "glass-card-active" : ""}`}
      style={{ overflow: "visible", zIndex: "auto" }}>
      {/* ===== HEADER ROW ===== */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="flex items-center justify-center w-6 h-6 rounded-md text-xs font-bold"
            style={{ background: "var(--accent-soft)", color: "var(--accent-primary)" }}>
            {index + 1}
          </div>
          <span className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
            Tarjeta de Aprendizaje
          </span>
        </div>

        <div className="flex items-center gap-1">
          <button onClick={onMoveUp} disabled={index === 0}
            className="btn-ghost px-2 py-1.5 disabled:opacity-30" title="Mover arriba">
            <ChevronUp size={14} />
          </button>
          <button onClick={onMoveDown} disabled={index === total - 1}
            className="btn-ghost px-2 py-1.5 disabled:opacity-30" title="Mover abajo">
            <ChevronDown size={14} />
          </button>
          <button onClick={onDuplicate} className="btn-ghost px-2 py-1.5" title="Duplicar">
            <Copy size={14} />
          </button>
          <button onClick={onRemove} disabled={total === 1}
            className="btn-danger px-2 py-1.5 disabled:opacity-30" title="Eliminar">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* ===== SPANISH SECTION ===== */}
      <div className="mb-4" style={{ overflow: "visible" }}>
        <div className="flex items-center gap-2 mb-2">
          <Mic size={14} style={{ color: "var(--accent-primary)" }} />
          <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "var(--accent-primary)" }}>
            Español
          </span>
        </div>
        <textarea
          id={`block-text-es-${uid}`}
          className="input-field mb-3"
          placeholder="Escribí la frase en español…"
          value={block.text}
          onChange={(e) => onUpdate({ text: e.target.value })}
          rows={2}
        />
        <div className="grid gap-3" style={{ gridTemplateColumns: "1fr 1fr", overflow: "visible" }}>
          <VoiceSelector
            uid={`es-${uid}`}
            label="Voz Español"
            langPrefix="es"
            voices={edgeVoices}
            loading={voicesLoading}
            selectedVoice={block.voice}
            onVoiceChange={(v) => onUpdate({ voice: v })}
            accentColor="var(--accent-primary)"
          />
          {/* Rate & Pitch — solo para motor Edge */}
          {engine === "edge" && (
          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="flex justify-between text-xs font-medium mb-1">
                <span style={{ color: "var(--text-muted)" }}>Velocidad</span>
                <span style={{ color: "var(--accent-primary)", fontVariantNumeric: "tabular-nums" }}>
                  {block.rate >= 0 ? "+" : ""}{block.rate}%
                </span>
              </label>
              <input
                id={`block-rate-${uid}`}
                type="range" className="range-slider"
                min={-50} max={100} step={5}
                value={block.rate}
                onChange={(e) => onUpdate({ rate: parseInt(e.target.value) })}
              />
            </div>
            <div>
              <label className="flex justify-between text-xs font-medium mb-1">
                <span style={{ color: "var(--text-muted)" }}>Tono</span>
                <span style={{ color: "var(--accent-secondary)", fontVariantNumeric: "tabular-nums" }}>
                  {block.pitch >= 0 ? "+" : ""}{block.pitch}Hz
                </span>
              </label>
              <input
                id={`block-pitch-${uid}`}
                type="range" className="range-slider"
                min={-20} max={20} step={2}
                value={block.pitch}
                onChange={(e) => onUpdate({ pitch: parseInt(e.target.value) })}
              />
            </div>
          </div>
          )}
        </div>

        {/* ===== EQ SECTION (collapsible) ===== */}
        <EQSection uid={uid} block={block} onUpdate={onUpdate} />
      </div>

      {/* ===== DIVIDER ===== */}
      <div className="flex items-center gap-3 my-4">
        <div className="flex-1 h-px" style={{ background: "var(--border-subtle)" }} />
        <Clock size={12} style={{ color: "var(--text-muted)" }} />
        <div className="flex items-center gap-2">
          <label className="text-xs" style={{ color: "var(--text-muted)" }}>Pausa</label>
          <select
            id={`block-pause-${uid}`}
            className="input-field py-1 px-2 text-xs"
            style={{ width: "auto", minWidth: "60px" }}
            value={block.pauseDuration}
            onChange={(e) => onUpdate({ pauseDuration: parseFloat(e.target.value) })}>
            {[0, 1, 2, 3, 4, 5, 7, 10].map((s) => (
              <option key={s} value={s}>{s}s</option>
            ))}
          </select>
        </div>
        <div className="flex-1 h-px" style={{ background: "var(--border-subtle)" }} />
      </div>

      {/* ===== ENGLISH SECTION ===== */}
      <div style={{ overflow: "visible" }}>
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Globe size={14} style={{ color: "#60a5fa" }} />
            <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: "#60a5fa" }}>
              English
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Repeat size={12} style={{ color: "var(--text-muted)" }} />
            <label className="text-xs" style={{ color: "var(--text-muted)" }}>Repetir</label>
            <select
              id={`block-reps-${uid}`}
              className="input-field py-1 px-2 text-xs"
              style={{ width: "auto", minWidth: "50px" }}
              value={block.repsEn}
              onChange={(e) => onUpdate({ repsEn: parseInt(e.target.value) })}>
              {[1, 2, 3, 4, 5].map((n) => (
                <option key={n} value={n}>{n}x</option>
              ))}
            </select>
          </div>
        </div>
        <textarea
          id={`block-text-en-${uid}`}
          className="input-field mb-3"
          placeholder="Write the English translation…"
          value={block.textEn}
          onChange={(e) => onUpdate({ textEn: e.target.value })}
          rows={2}
          style={{ borderColor: hasEnglish ? "rgba(96, 165, 250, 0.3)" : undefined }}
        />
        <div className="grid gap-3" style={{ overflow: "visible" }}>
          <VoiceSelector
            uid={`en-${uid}`}
            label="English Voice"
            langPrefix="en"
            voices={voices}
            loading={voicesLoading}
            selectedVoice={block.voiceEn}
            onVoiceChange={(v) => onUpdate({ voiceEn: v })}
            accentColor="#60a5fa"
          />
        </div>
      </div>
    </div>
  );
}
