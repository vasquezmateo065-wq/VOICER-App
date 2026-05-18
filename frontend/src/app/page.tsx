"use client";

import { Mic2, Plus, Wand2, Timer, Zap, Cpu, RefreshCw, AlertCircle } from "lucide-react";
import { useBlocks } from "@/hooks/useBlocks";
import { api, BackendUnreachableError, VoicerAPIError } from "@/lib/api";
import { Voice } from "@/types";
import { useEffect, useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AudioBlock from "@/components/AudioBlock";
import AudioPlayer from "@/components/AudioPlayer";

type Engine = "edge" | "nvidia";

export default function HomePage() {
  const { blocks, addBlock, removeBlock, updateBlock, duplicateBlock, moveBlock } = useBlocks();

  // Voices state — split by engine
  const [edgeVoices, setEdgeVoices] = useState<Voice[]>([]);
  const [nvidiaVoices, setNvidiaVoices] = useState<Voice[]>([]);
  const [voicesLoading, setVoicesLoading] = useState(true);

  // Engine & production controls
  const [engine, setEngine] = useState<Engine>("edge");
  const [nvidiaAvailable, setNvidiaAvailable] = useState(false);
  const [nvidiaError, setNvidiaError] = useState<string | null>(null);
  const [transitionPause, setTransitionPause] = useState(2);

  // Output state
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const playerRef = useRef<HTMLDivElement>(null);

  // Cleanup ObjectURL on unmount
  useEffect(() => {
    return () => { if (audioUrl) URL.revokeObjectURL(audioUrl); };
  }, [audioUrl]);

  // Load voices & check NVIDIA status on mount
  const loadVoices = useCallback(async () => {
    setVoicesLoading(true);
    setError(null);

    // 1. Edge voices — crítico, mostramos error si falla
    try {
      const edgeData = await api.voices();
      setEdgeVoices(edgeData.voices);
    } catch (err) {
      if (err instanceof BackendUnreachableError) {
        setError(err.message);
      } else {
        setError(`Error al cargar voces: ${err instanceof Error ? err.message : "Error desconocido"}`);
      }
      setVoicesLoading(false);
      return; // Sin backend no seguimos
    }

    // 2. NVIDIA status — opcional, no bloquea si falla
    try {
      const nvidiaStatus = await api.nvidiaStatus();
      setNvidiaAvailable(nvidiaStatus.configured);
      setNvidiaError(null);

      if (nvidiaStatus.configured) {
        const nvidiaData = await api.nvidiaVoices();
        setNvidiaVoices(nvidiaData.voices);
      }
    } catch (err) {
      // NVIDIA no disponible — el toggle queda bloqueado
      setNvidiaAvailable(false);
      if (err instanceof BackendUnreachableError) {
        // No mostramos error de NVIDIA si ya hay error de backend (es redundante)
      } else {
        setNvidiaError(err instanceof Error ? err.message : "No se pudo verificar el motor NVIDIA");
      }
    }

    setVoicesLoading(false);
  }, []);

  useEffect(() => {
    loadVoices();
  }, [loadVoices]);

  // The active voice list depends on selected engine
  const activeVoices = engine === "nvidia" ? nvidiaVoices : edgeVoices;

  // Voice sync: when engine changes, auto-correct any block voices not valid for the new engine
  const prevEngineRef = useRef(engine);
  useEffect(() => {
    if (voicesLoading) return;
    if (prevEngineRef.current === engine) return;
    prevEngineRef.current = engine;

    const voices = engine === "nvidia" ? nvidiaVoices : edgeVoices;
    if (voices.length === 0) return;

    const esVoices = voices.filter((v) => v.language.startsWith("es"));
    const enVoices = voices.filter((v) => v.language.startsWith("en"));

    blocks.forEach((block) => {
      if (!voices.some((v) => v.name === block.voice) && esVoices.length > 0) {
        updateBlock(block.id, { voice: esVoices[0].name });
      }
      if (!voices.some((v) => v.name === block.voiceEn) && enVoices.length > 0) {
        updateBlock(block.id, { voiceEn: enVoices[0].name });
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [engine, voicesLoading]);

  const handleGenerate = async () => {
    const emptyBlock = blocks.find((b) => !b.text.trim());
    if (emptyBlock) {
      setError("Hay bloques con texto en español vacío. Completá todos antes de generar.");
      return;
    }

    setIsGenerating(true);
    setError(null);

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    try {
      const payload = {
        blocks: blocks.map((b) => ({
          text: b.text,
          text_en: b.textEn,
          voice: b.voice,
          voice_en: b.voiceEn,
          rate: `${b.rate >= 0 ? "+" : ""}${b.rate}%`,
          pitch: `${b.pitch >= 0 ? "+" : ""}${b.pitch}Hz`,
          pause_duration: b.pauseDuration,
          reps_en: b.repsEn,
          bass: b.bass,
          treble: b.treble,
        })),
        transition_pause: transitionPause,
        engine,
      };

      const result = await api.generate(payload);

      if (result.blob) {
        setAudioUrl(URL.createObjectURL(result.blob));
      } else if (result.audio_path) {
        setAudioUrl(`${process.env.NEXT_PUBLIC_API_URL}/api/audio/${encodeURIComponent(result.audio_path)}`);
      }

      setTimeout(() => playerRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
    } catch (err) {
      let msg = "Error desconocido generando audio.";
      if (err instanceof BackendUnreachableError) {
        msg = err.message;
      } else if (err instanceof VoicerAPIError) {
        msg = `El servidor respondió con error (${err.statusCode}):\n${err.message}`;
      } else if (err instanceof Error) {
        msg = err.message;
      }
      setError(msg);
    } finally {
      setIsGenerating(false);
    }
  };

  const filledBlocks = blocks.filter((b) => b.text.trim()).length;
  const totalChars = blocks.reduce((acc, b) => acc + b.text.length + b.textEn.length, 0);

  return (
    <div className="min-h-screen">
      {/* ===== HEADER ===== */}
      <header style={{ borderBottom: "1px solid var(--border-subtle)", backdropFilter: "blur(20px)" }}
        className="sticky top-0 z-20 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-9 h-9 rounded-xl"
              style={{ background: "linear-gradient(135deg, var(--accent-primary), #7c3aed)" }}>
              <Mic2 size={18} color="white" />
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight" style={{ color: "var(--text-primary)" }}>
                VOICER
              </h1>
              <p className="text-xs" style={{ color: "var(--text-muted)" }}>Text to Speech Premium</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Engine badge in header */}
            {engine === "nvidia" && (
              <span className="badge" style={{ background: "rgba(52,211,153,0.15)", color: "#34d399", border: "1px solid rgba(52,211,153,0.3)" }}>
                ✦ NVIDIA
              </span>
            )}
            <span className="badge badge-violet">{blocks.length} tarjeta{blocks.length !== 1 ? "s" : ""}</span>
            {totalChars > 0 && (
              <span className="text-xs" style={{ color: "var(--text-muted)" }}>{totalChars.toLocaleString()} chars</span>
            )}
          </div>
        </div>
      </header>

      {/* ===== MAIN CONTENT ===== */}
      <main className="max-w-4xl mx-auto px-6 py-8">

        {/* Error banner */}
        {error && (
          <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
            className="mb-6 p-5 rounded-xl"
            style={{
              background: "rgba(239,68,68,0.08)",
              border: "1px solid rgba(239,68,68,0.25)",
            }}>
            <div className="flex items-start gap-3">
              <AlertCircle size={18} style={{ color: "#f87171", marginTop: 1, flexShrink: 0 }} />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold mb-1" style={{ color: "#fca5a5" }}>
                  {error.includes("No se pudo conectar") ? "Backend no disponible" : "Error"}
                </p>
                <p className="text-sm whitespace-pre-line" style={{ color: "#f87171" }}>
                  {error}
                </p>
                {error.includes("No se pudo conectar") && (
                  <button
                    onClick={() => loadVoices()}
                    className="mt-3 flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-medium transition-all hover:opacity-80"
                    style={{ background: "rgba(239,68,68,0.15)", color: "#fca5a5", border: "1px solid rgba(239,68,68,0.3)" }}>
                    <RefreshCw size={13} />
                    Reintentar conexión
                  </button>
                )}
              </div>
              <button
                onClick={() => setError(null)}
                className="text-xs px-2 py-1 rounded hover:opacity-70 flex-shrink-0"
                style={{ color: "var(--text-muted)" }}>
                ✕
              </button>
            </div>
          </motion.div>
        )}

        {/* ===== BLOCK LIST ===== */}
        <section className="space-y-3 mb-6">
          <AnimatePresence mode="popLayout">
            {blocks.map((block, index) => (
              <motion.div key={block.id}
                initial={{ opacity: 0, y: 20, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, x: -20, scale: 0.97 }}
                transition={{ duration: 0.2 }}
                style={{ position: "relative", zIndex: blocks.length - index }}
                layout>
                <AudioBlock
                  block={block}
                  index={index}
                  total={blocks.length}
                  voices={activeVoices}
                  edgeVoices={edgeVoices}
                  voicesLoading={voicesLoading}
                  engine={engine}
                  onUpdate={(patch) => updateBlock(block.id, patch)}
                  onRemove={() => removeBlock(block.id)}
                  onDuplicate={() => duplicateBlock(block.id)}
                  onMoveUp={() => moveBlock(block.id, "up")}
                  onMoveDown={() => moveBlock(block.id, "down")}
                />
              </motion.div>
            ))}
          </AnimatePresence>
        </section>

        {/* ===== ADD BLOCK ===== */}
        <motion.button
          onClick={addBlock}
          className="btn-ghost w-full py-3 mb-8"
          style={{ borderStyle: "dashed" }}
          whileHover={{ scale: 1.005 }}
          whileTap={{ scale: 0.998 }}>
          <Plus size={16} />
          Agregar tarjeta de aprendizaje
        </motion.button>

        {/* ===== CONTROL PANEL ===== */}
        <div className="glass-card p-6 mb-6">
          <h2 className="font-semibold text-sm mb-5" style={{ color: "var(--text-secondary)" }}>
            CONTROL DE PRODUCCIÓN
          </h2>

          {/* ── Engine Toggle ── */}
          <div className="mb-6">
            <p className="text-xs font-medium mb-3" style={{ color: "var(--text-muted)" }}>Motor de Síntesis</p>
            <div className="grid grid-cols-2 gap-2">
              {/* Edge button */}
              <button
                type="button"
                onClick={() => setEngine("edge")}
                className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-medium transition-all ${engine === "edge" ? "ring-1" : "opacity-60 hover:opacity-80"}`}
                style={engine === "edge"
                  ? { background: "var(--accent-soft)", color: "var(--accent-primary)" }
                  : { background: "rgba(255,255,255,0.04)", color: "var(--text-muted)" }
                }>
                <Zap size={15} />
                <div className="text-left">
                  <div className="font-semibold">Estándar</div>
                  <div className="text-xs opacity-70">Edge-TTS · 322 voces</div>
                </div>
              </button>

              {/* NVIDIA button */}
              <button
                type="button"
                onClick={() => nvidiaAvailable && setEngine("nvidia")}
                disabled={!nvidiaAvailable}
                className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm font-medium transition-all ${engine === "nvidia" ? "ring-1" : nvidiaAvailable ? "opacity-60 hover:opacity-80" : "opacity-30 cursor-not-allowed"}`}
                style={engine === "nvidia"
                  ? { background: "rgba(52,211,153,0.12)", color: "#34d399" }
                  : { background: "rgba(255,255,255,0.04)", color: "var(--text-muted)" }
                }>
                <Cpu size={15} />
                <div className="text-left">
                  <div className="font-semibold">Premium ✦</div>
                  <div className="text-xs opacity-70">
                    {nvidiaAvailable ? "NVIDIA · IA Generativa" : "Requiere API Key"}
                  </div>
                </div>
              </button>
            </div>
            {!nvidiaAvailable && (
              <div className="mt-2">
                {nvidiaError ? (
                  <div className="flex items-start gap-2">
                    <AlertCircle size={12} style={{ color: "#f87171", marginTop: 2, flexShrink: 0 }} />
                    <div>
                      <p className="text-xs" style={{ color: "#f87171" }}>{nvidiaError}</p>
                      <button
                        onClick={() => loadVoices()}
                        className="text-xs mt-1 underline hover:opacity-70"
                        style={{ color: "var(--text-muted)" }}>
                        Reintentar
                      </button>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs" style={{ color: "var(--text-muted)" }}>
                    Para activar el motor Premium, configurá <code className="px-1 py-0.5 rounded" style={{ background: "rgba(255,255,255,0.08)" }}>NVIDIA_API_KEY</code> en <code className="px-1 py-0.5 rounded" style={{ background: "rgba(255,255,255,0.08)" }}>backend/.env</code>
                  </p>
                )}
              </div>
            )}
          </div>

          {/* ── Transition Pause ── */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-3">
              <Timer size={14} style={{ color: "var(--text-muted)" }} />
              <label className="text-xs font-medium" style={{ color: "var(--text-muted)" }}>
                Pausa entre tarjetas
              </label>
            </div>
            <div className="flex items-center gap-4">
              <input
                id="transition-pause"
                type="range"
                className="range-slider flex-1"
                min={0} max={10} step={0.5}
                value={transitionPause}
                onChange={(e) => setTransitionPause(parseFloat(e.target.value))}
              />
              <span className="text-sm font-medium min-w-[3rem] text-right"
                style={{ color: "var(--accent-primary)", fontVariantNumeric: "tabular-nums" }}>
                {transitionPause}s
              </span>
            </div>
            <p className="text-xs mt-1.5" style={{ color: "var(--text-muted)" }}>
              Silencio de transición al pasar de una tarjeta a la siguiente.
            </p>
          </div>

          {/* ── Generate Button ── */}
          <motion.button
            onClick={handleGenerate}
            disabled={isGenerating || filledBlocks === 0}
            className="btn-primary w-full py-4 text-base"
            style={engine === "nvidia" ? {
              background: "linear-gradient(135deg, #059669, #34d399)",
            } : {}}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}>
            {isGenerating ? (
              <>
                <div className="spinner" />
                {engine === "nvidia" ? "Generando con IA…" : "Generando audio…"}
              </>
            ) : (
              <>
                <Wand2 size={18} />
                Generar Audio {filledBlocks > 0 ? `(${filledBlocks} tarjeta${filledBlocks !== 1 ? "s" : ""})` : ""}
              </>
            )}
          </motion.button>
        </div>

        {/* ===== AUDIO PLAYER ===== */}
        <div ref={playerRef}>
          <AnimatePresence>
            {audioUrl && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}>
                <AudioPlayer url={audioUrl} />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
