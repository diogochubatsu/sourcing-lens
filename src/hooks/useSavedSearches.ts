'use client';

import { useState, useCallback } from 'react';

const STORAGE_KEY = 'arbitlens_saved_searches';
const MAX_SAVED = 20;

export interface SavedSearch {
  query: string;
  savedAt: number;
  lastChecked?: number;
}

export function useSavedSearches() {
  const [saved, setSaved] = useState<SavedSearch[]>(() => {
    if (typeof window === 'undefined') return [];
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  });

  const saveSearch = useCallback((query: string) => {
    if (!query.trim()) return;
    setSaved(prev => {
      const exists = prev.find(s => s.query === query);
      if (exists) {
        return prev.map(s => s.query === query ? { ...s, savedAt: Date.now() } : s);
      }
      const next = [{ query, savedAt: Date.now() }, ...prev].slice(0, MAX_SAVED);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  }, []);

  const removeSearch = useCallback((query: string) => {
    setSaved(prev => {
      const next = prev.filter(s => s.query !== query);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {}
      return next;
    });
  }, []);

  const isSaved = useCallback((query: string) => {
    return saved.some(s => s.query === query);
  }, [saved]);

  const clearSaved = useCallback(() => {
    setSaved([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {}
  }, []);

  return { saved, saveSearch, removeSearch, isSaved, clearSaved };
}
