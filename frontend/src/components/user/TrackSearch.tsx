import { useState, useCallback } from "react";
import { Search, X, Music } from "lucide-react";
import type { Track } from "../../types";
import api from "../../services/api";

interface TrackSearchProps {
  onSelect: (track: { name: string; artist: string }) => void;
  selectedTracks: { name: string; artist: string }[];
  maxTracks?: number;
}

export default function TrackSearch({
  onSelect,
  selectedTracks,
  maxTracks = 3,
}: TrackSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<Track[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const tracks = await api.searchTracks(searchQuery, 10, "dataset");
      setResults(tracks);
      setShowResults(true);
    } catch (error) {
      console.error("Search error:", error);
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);

    // Debounce search
    const timeoutId = setTimeout(() => {
      handleSearch(value);
    }, 300);

    return () => clearTimeout(timeoutId);
  };

  const handleSelectTrack = (track: Track) => {
    if (selectedTracks.length >= maxTracks) return;

    onSelect({ name: track.name, artist: track.artist });
    setQuery("");
    setResults([]);
    setShowResults(false);
  };

  const isTrackSelected = (track: Track) => {
    return selectedTracks.some(
      (t) =>
        t.name.toLowerCase() === track.name.toLowerCase() &&
        t.artist.toLowerCase() === track.artist.toLowerCase(),
    );
  };

  return (
    <div className="relative">
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder="Search for a seed track..."
          className="w-full pl-12 pr-4 py-3 bg-[var(--surface)] border border-white/10 rounded-xl text-white placeholder-[var(--text-muted)] focus:outline-none focus:border-[var(--primary)] transition-colors"
          disabled={selectedTracks.length >= maxTracks}
        />
        {isSearching && (
          <div className="absolute right-4 top-1/2 -translate-y-1/2">
            <div className="w-5 h-5 border-2 border-[var(--primary)] border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {/* Search Results Dropdown */}
      {showResults && results.length > 0 && (
        <div className="absolute z-50 w-full mt-2 bg-[var(--surface)] border border-white/10 rounded-xl shadow-xl max-h-64 overflow-y-auto">
          {results.map((track, index) => {
            const selected = isTrackSelected(track);
            return (
              <button
                key={`${track.name}-${track.artist}-${index}`}
                onClick={() => !selected && handleSelectTrack(track)}
                disabled={selected}
                className={`
                  w-full flex items-center gap-3 px-4 py-3 text-left transition-colors
                  ${selected ? "opacity-50 cursor-not-allowed" : "hover:bg-white/5"}
                  ${index !== results.length - 1 ? "border-b border-white/5" : ""}
                `}
              >
                <div className="w-10 h-10 rounded-lg bg-[var(--surface-light)] flex items-center justify-center flex-shrink-0">
                  <Music className="w-5 h-5 text-[var(--text-muted)]" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-white truncate">
                    {track.name}
                  </p>
                  <p className="text-xs text-[var(--text-muted)] truncate">
                    {track.artist}
                  </p>
                </div>
                {selected && (
                  <span className="text-xs text-[var(--primary)]">
                    Selected
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Click outside to close */}
      {showResults && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowResults(false)}
        />
      )}

      {selectedTracks.length >= maxTracks && (
        <p className="mt-2 text-xs text-[var(--text-muted)]">
          Maximum {maxTracks} seed tracks selected
        </p>
      )}
    </div>
  );
}

interface SelectedTracksProps {
  tracks: { name: string; artist: string }[];
  onRemove: (index: number) => void;
}

export function SelectedTracks({ tracks, onRemove }: SelectedTracksProps) {
  if (tracks.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-3">
      {tracks.map((track, index) => (
        <div
          key={`${track.name}-${track.artist}`}
          className="flex items-center gap-2 px-3 py-1.5 bg-[var(--primary)]/20 rounded-full"
        >
          <span className="text-sm text-[var(--primary)]">
            {track.name} - {track.artist}
          </span>
          <button
            onClick={() => onRemove(index)}
            className="p-0.5 rounded-full hover:bg-[var(--primary)]/30 transition-colors"
          >
            <X className="w-3 h-3 text-[var(--primary)]" />
          </button>
        </div>
      ))}
    </div>
  );
}
