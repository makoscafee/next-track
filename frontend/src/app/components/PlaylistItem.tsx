import React from 'react';
import { Track } from './TrackCard';
import { Play, Pause, Music } from 'lucide-react';
import { Badge } from './ui/badge';

interface PlaylistItemProps {
  track: Track;
  index: number;
  isActive: boolean;
  isPlaying: boolean;
  onSelect: () => void;
}

export function PlaylistItem({ track, index, isActive, isPlaying, onSelect }: PlaylistItemProps) {
  return (
    <div
      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-all ${
        isActive 
          ? 'bg-primary/10 border border-primary/20' 
          : 'hover:bg-muted'
      }`}
      onClick={onSelect}
    >
      {/* Index/Play Button */}
      <div className="flex-shrink-0 w-8 text-center">
        {isActive && isPlaying ? (
          <div className="flex items-center justify-center">
            <Pause className="w-4 h-4 text-primary fill-primary" />
          </div>
        ) : isActive ? (
          <div className="flex items-center justify-center">
            <Play className="w-4 h-4 text-primary fill-primary" />
          </div>
        ) : (
          <span className="text-sm text-muted-foreground">{index + 1}</span>
        )}
      </div>

      {/* Album Art */}
      <div className="flex-shrink-0">
        <img
          src={track.imageUrl}
          alt={track.album}
          className="w-12 h-12 rounded object-cover"
        />
      </div>

      {/* Track Info */}
      <div className="flex-1 min-w-0">
        <div className={`font-medium truncate ${isActive ? 'text-primary' : ''}`}>
          {track.title}
        </div>
        <div className="text-sm text-muted-foreground truncate">
          {track.artist}
        </div>
      </div>

      {/* Preview indicator + Match Score */}
      <div className="flex-shrink-0 flex items-center gap-1.5">
        {track.previewUrl && (
          <Music className="w-3 h-3 text-purple-400" title="Preview available" />
        )}
        <Badge variant={isActive ? 'default' : 'secondary'} className="text-xs">
          {track.matchScore}%
        </Badge>
      </div>
    </div>
  );
}
