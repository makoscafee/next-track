import React from 'react';
import { Badge } from './ui/badge';

const GENRES = [
  'pop', 'rock', 'hip-hop', 'r&b', 'electronic', 'jazz',
  'classical', 'country', 'latin', 'metal', 'indie', 'soul',
];

interface GenreFilterProps {
  selected: string[];
  onChange: (genres: string[]) => void;
}

export function GenreFilter({ selected, onChange }: GenreFilterProps) {
  const toggle = (genre: string) => {
    if (selected.includes(genre)) {
      onChange(selected.filter((g) => g !== genre));
    } else {
      onChange([...selected, genre]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">Genre filter</span>
        <span className="text-xs text-muted-foreground">(optional — picks stay in recommendation)</span>
      </div>
      <div className="flex flex-wrap gap-1.5">
        {GENRES.map((genre) => {
          const active = selected.includes(genre);
          return (
            <button
              key={genre}
              onClick={() => toggle(genre)}
              className="focus:outline-none"
              type="button"
            >
              <Badge
                variant={active ? 'default' : 'outline'}
                className={`cursor-pointer capitalize transition-colors ${
                  active
                    ? 'bg-purple-600 hover:bg-purple-700 text-white border-purple-600'
                    : 'hover:border-purple-400 hover:text-purple-600'
                }`}
              >
                {genre}
              </Badge>
            </button>
          );
        })}
        {selected.length > 0 && (
          <button
            onClick={() => onChange([])}
            className="text-xs text-muted-foreground hover:text-red-500 transition-colors ml-1 self-center"
            type="button"
          >
            clear
          </button>
        )}
      </div>
    </div>
  );
}
