import React, { useState, useEffect, useRef } from 'react';
import { Search, X, Music } from 'lucide-react';
import { searchTracksWithPreview } from '../../services/api';
import type { DeezerSearchResult } from '../../services/types';

export interface SeedTrack {
  name: string;
  artist: string;
  imageUrl?: string;
  previewUrl?: string;
}

interface SeedTrackSearchProps {
  seeds: SeedTrack[];
  onSeedsChange: (seeds: SeedTrack[]) => void;
  maxSeeds?: number;
}

export function SeedTrackSearch({ seeds, onSeedsChange, maxSeeds = 3 }: SeedTrackSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<DeezerSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setShowDropdown(false);
      return;
    }
    debounceRef.current = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await searchTracksWithPreview(query.trim(), 6);
        setResults(res);
        setShowDropdown(res.length > 0);
      } catch {
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 400);
  }, [query]);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setShowDropdown(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const addSeed = (result: DeezerSearchResult) => {
    if (seeds.length >= maxSeeds) return;
    const name = result.title ?? result.name ?? '';
    const artist = result.artist ?? '';
    if (seeds.some((s) => s.name === name && s.artist === artist)) return;
    onSeedsChange([
      ...seeds,
      {
        name,
        artist,
        imageUrl: result.cover_small ?? result.cover_medium,
        previewUrl: result.preview_url,
      },
    ]);
    setQuery('');
    setShowDropdown(false);
  };

  const removeSeed = (index: number) => {
    onSeedsChange(seeds.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">Seed tracks</span>
        <span className="text-xs text-muted-foreground">(up to {maxSeeds}, optional)</span>
      </div>

      {/* Selected seeds */}
      {seeds.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {seeds.map((seed, i) => (
            <div
              key={i}
              className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-purple-100 dark:bg-purple-900/40 text-purple-800 dark:text-purple-200 text-xs font-medium"
            >
              {seed.imageUrl ? (
                <img src={seed.imageUrl} alt="" className="w-4 h-4 rounded-full object-cover" />
              ) : (
                <Music className="w-3.5 h-3.5" />
              )}
              <span className="max-w-32 truncate">{seed.name}</span>
              <span className="text-purple-500">·</span>
              <span className="max-w-24 truncate text-purple-600 dark:text-purple-400">{seed.artist}</span>
              <button
                onClick={() => removeSeed(i)}
                className="ml-0.5 hover:text-red-500 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Search input */}
      {seeds.length < maxSeeds && (
        <div ref={containerRef} className="relative">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground pointer-events-none" />
            <input
              type="text"
              className="w-full pl-9 pr-3 py-2 rounded-md border border-input bg-background text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500"
              placeholder="Search for a track to seed from…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onFocus={() => results.length > 0 && setShowDropdown(true)}
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>

          {/* Dropdown results */}
          {showDropdown && (
            <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-popover border border-border rounded-md shadow-lg overflow-hidden">
              {results.map((result, i) => (
                <button
                  key={i}
                  className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-muted transition-colors text-left"
                  onClick={() => addSeed(result)}
                >
                  {result.cover_small ? (
                    <img
                      src={result.cover_small}
                      alt=""
                      className="w-9 h-9 rounded object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-9 h-9 rounded bg-muted flex items-center justify-center flex-shrink-0">
                      <Music className="w-4 h-4 text-muted-foreground" />
                    </div>
                  )}
                  <div className="min-w-0">
                    <div className="text-sm font-medium truncate">
                      {result.title ?? result.name}
                    </div>
                    <div className="text-xs text-muted-foreground truncate">
                      {result.artist} {result.album ? `· ${result.album}` : ''}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
