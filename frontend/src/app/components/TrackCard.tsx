import React from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Play, Heart, Share2 } from 'lucide-react';
import { Button } from './ui/button';

export interface Track {
  id: string;
  title: string;
  artist: string;
  album: string;
  imageUrl: string;
  matchScore: number;
  audioFeatures: {
    valence: number;
    energy: number;
    danceability: number;
    tempo: number;
  };
  reason: string;
  previewUrl?: string;
}

interface TrackCardProps {
  track: Track;
}

export function TrackCard({ track }: TrackCardProps) {
  return (
    <Card className="overflow-hidden hover:shadow-lg transition-shadow">
      <div className="p-4">
        <div className="flex gap-4">
          {/* Album Art */}
          <div className="flex-shrink-0">
            <img
              src={track.imageUrl}
              alt={track.album}
              className="w-24 h-24 rounded-md object-cover"
            />
          </div>

          {/* Track Info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold truncate">{track.title}</h3>
                <p className="text-sm text-muted-foreground truncate">{track.artist}</p>
              </div>
              <Badge variant="secondary" className="flex-shrink-0">
                {track.matchScore}% Match
              </Badge>
            </div>

            {/* Audio Features */}
            <div className="space-y-2 mb-3">
              <div className="flex items-center gap-2 text-xs">
                <span className="w-20 text-muted-foreground">Valence</span>
                <Progress value={track.audioFeatures.valence} className="flex-1" />
                <span className="w-8 text-right">{track.audioFeatures.valence}%</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-20 text-muted-foreground">Energy</span>
                <Progress value={track.audioFeatures.energy} className="flex-1" />
                <span className="w-8 text-right">{track.audioFeatures.energy}%</span>
              </div>
              <div className="flex items-center gap-2 text-xs">
                <span className="w-20 text-muted-foreground">Dance</span>
                <Progress value={track.audioFeatures.danceability} className="flex-1" />
                <span className="w-8 text-right">{track.audioFeatures.danceability}%</span>
              </div>
            </div>

            {/* Reason */}
            <p className="text-xs text-muted-foreground italic mb-3 line-clamp-2">
              {track.reason}
            </p>

            {/* Actions */}
            <div className="flex gap-2">
              <Button size="sm" className="flex-1">
                <Play className="w-4 h-4 mr-1" />
                Play
              </Button>
              <Button size="sm" variant="outline">
                <Heart className="w-4 h-4" />
              </Button>
              <Button size="sm" variant="outline">
                <Share2 className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
