"use client";

import { useState, useCallback } from "react";
import { AudioBlock } from "@/types";

// Defaults Edge (motor Estándar). Al cambiar a NVIDIA, el sync en page.tsx los actualiza automáticamente.
const DEFAULT_VOICE_ES = "es-AR-ElenaNeural";
const DEFAULT_VOICE_EN = "en-US-JennyNeural";

function generateId(): string {
  return Math.random().toString(36).slice(2, 9);
}

function createBlock(overrides?: Partial<AudioBlock>): AudioBlock {
  return {
    id: generateId(),
    text: "",
    textEn: "",
    voice: DEFAULT_VOICE_ES,
    voiceEn: DEFAULT_VOICE_EN,
    rate: 0,
    pitch: 0,
    pauseDuration: 3,
    repsEn: 2,
    bass: 0,
    treble: 0,
    ...overrides,
  };
}

export function useBlocks() {
  const [blocks, setBlocks] = useState<AudioBlock[]>([createBlock()]);

  const addBlock = useCallback(() => {
    setBlocks((prev) => {
      // Hereda voces del último bloque para velocidad
      const last = prev.at(-1);
      return [...prev, createBlock({
        voice: last?.voice ?? DEFAULT_VOICE_ES,
        voiceEn: last?.voiceEn ?? DEFAULT_VOICE_EN,
        pauseDuration: last?.pauseDuration ?? 3,
        repsEn: last?.repsEn ?? 2,
        bass: last?.bass ?? 0,
        treble: last?.treble ?? 0,
      })];
    });
  }, []);

  const removeBlock = useCallback((id: string) => {
    setBlocks((prev) => (prev.length > 1 ? prev.filter((b) => b.id !== id) : prev));
  }, []);

  const updateBlock = useCallback((id: string, patch: Partial<AudioBlock>) => {
    setBlocks((prev) =>
      prev.map((b) => (b.id === id ? { ...b, ...patch } : b))
    );
  }, []);

  const duplicateBlock = useCallback((id: string) => {
    setBlocks((prev) => {
      const idx = prev.findIndex((b) => b.id === id);
      if (idx === -1) return prev;
      const clone = { ...prev[idx], id: generateId() };
      const next = [...prev];
      next.splice(idx + 1, 0, clone);
      return next;
    });
  }, []);

  const moveBlock = useCallback((id: string, direction: "up" | "down") => {
    setBlocks((prev) => {
      const idx = prev.findIndex((b) => b.id === id);
      if (idx === -1) return prev;
      const next = [...prev];
      const targetIdx = direction === "up" ? idx - 1 : idx + 1;
      if (targetIdx < 0 || targetIdx >= next.length) return prev;
      [next[idx], next[targetIdx]] = [next[targetIdx], next[idx]];
      return next;
    });
  }, []);

  const clearBlocks = useCallback(() => {
    setBlocks([createBlock()]);
  }, []);

  return { blocks, addBlock, removeBlock, updateBlock, duplicateBlock, moveBlock, clearBlocks };
}
