import React, { useRef, useEffect, useState } from 'react';
import { Track } from './TrackCard';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Progress } from './ui/progress';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  Heart,
  Share2,
  Volume2,
  Shuffle,
  Repeat,
  Music,
} from 'lucide-react';

interface NowPlayingProps {
  track: Track;
  isPlaying: boolean;
  onPlayPause: () => void;
  onNext: () => void;
  onPrevious: () => void;
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds) || isNaN(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function NowPlaying({ track, isPlaying, onPlayPause, onNext, onPrevious }: NowPlayingProps) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Sync audio src when track changes
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    setCurrentTime(0);
    setDuration(0);
    if (track.previewUrl) {
      audio.src = track.previewUrl;
      audio.load();
    } else {
      audio.src = '';
    }
  }, [track.previewUrl, track.id]);

  // Sync play/pause
  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !track.previewUrl) return;
    if (isPlaying) {
      audio.play().catch(() => {/* autoplay may be blocked */});
    } else {
      audio.pause();
    }
  }, [isPlaying, track.previewUrl, track.id]);

  const handleTimeUpdate = () => {
    const audio = audioRef.current;
    if (audio) setCurrentTime(audio.currentTime);
  };

  const handleLoadedMetadata = () => {
    const audio = audioRef.current;
    if (audio) setDuration(audio.duration);
  };

  const handleEnded = () => {
    onNext();
  };

  const handleSeek = (e: React.MouseEvent<HTMLDivElement>) => {
    const audio = audioRef.current;
    if (!audio || !duration) return;
    const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    audio.currentTime = ratio * duration;
  };

  const progressPercent = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="space-y-6">
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        preload="metadata"
      />

      {/* Album Art & Basic Info */}
      <div className="flex flex-col md:flex-row gap-6">
        {/* Large Album Art */}
        <div className="flex-shrink-0">
          <div className="relative group">
            <img
              src={track.imageUrl}
              alt={track.album}
              className="w-full md:w-80 h-auto aspect-square rounded-lg object-cover shadow-2xl"
            />
            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity rounded-lg flex items-center justify-center">
              <Button
                size="lg"
                className="w-16 h-16 rounded-full"
                onClick={onPlayPause}
              >
                {isPlaying ? (
                  <Pause className="w-8 h-8" />
                ) : (
                  <Play className="w-8 h-8 ml-1" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Track Details */}
        <div className="flex-1 flex flex-col justify-between">
          <div>
            <div className="mb-4">
              <div className="flex items-center gap-2 mb-1">
                <h2 className="text-3xl font-bold">{track.title}</h2>
                {track.previewUrl && (
                  <Music className="w-5 h-5 text-purple-500 flex-shrink-0" title="30s preview available" />
                )}
              </div>
              <p className="text-xl text-muted-foreground mb-1">{track.artist}</p>
              <p className="text-sm text-muted-foreground">{track.album}</p>
              {!track.previewUrl && (
                <p className="text-xs text-muted-foreground mt-2 italic">No preview available</p>
              )}
            </div>

            {/* Match Info */}
            <Card className="p-4 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20 border-green-200 dark:border-green-800">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-green-500 text-white flex items-center justify-center font-bold text-lg">
                  {track.matchScore}%
                </div>
                <div className="flex-1">
                  <div className="font-semibold text-green-900 dark:text-green-100 mb-1">
                    Perfect Match
                  </div>
                  <p className="text-sm text-green-700 dark:text-green-300">
                    {track.reason}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 mt-6">
            <Button className="flex-1 md:flex-none">
              <Heart className="w-4 h-4 mr-2" />
              Save to Library
            </Button>
            <Button variant="outline">
              <Share2 className="w-4 h-4 mr-2" />
              Share
            </Button>
          </div>
        </div>
      </div>

      {/* Audio Features Visualization */}
      <Card className="p-6">
        <h3 className="font-semibold mb-4">Audio Features Analysis</h3>
        <div className="flex flex-col md:flex-row items-center gap-6">
          {/* Radar chart */}
          <div className="flex-shrink-0 w-64 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart
                data={[
                  { feature: 'Positivity', value: track.audioFeatures.valence, fullMark: 100 },
                  { feature: 'Energy', value: track.audioFeatures.energy, fullMark: 100 },
                  { feature: 'Danceability', value: track.audioFeatures.danceability, fullMark: 100 },
                  { feature: 'Tempo', value: Math.min(Math.round(track.audioFeatures.tempo / 2), 100), fullMark: 100 },
                ]}
              >
                <PolarGrid className="stroke-muted" />
                <PolarAngleAxis
                  dataKey="feature"
                  tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                />
                <PolarRadiusAxis
                  angle={30}
                  domain={[0, 100]}
                  tick={false}
                  axisLine={false}
                />
                <Radar
                  name="Audio Features"
                  dataKey="value"
                  stroke="hsl(var(--primary))"
                  fill="hsl(var(--primary))"
                  fillOpacity={0.3}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                    color: 'hsl(var(--popover-foreground))',
                    fontSize: '12px',
                  }}
                  formatter={(value: number) => [`${value}%`, 'Value']}
                />
              </RadarChart>
            </ResponsiveContainer>
          </div>

          {/* Numeric breakdown */}
          <div className="flex-1 grid grid-cols-2 gap-x-8 gap-y-4 text-sm">
            {[
              { label: 'Valence', desc: 'Musical positiveness', value: track.audioFeatures.valence, unit: '%' },
              { label: 'Energy', desc: 'Intensity & activity', value: track.audioFeatures.energy, unit: '%' },
              { label: 'Danceability', desc: 'Suitability for dancing', value: track.audioFeatures.danceability, unit: '%' },
              { label: 'Tempo', desc: 'Speed in BPM', value: track.audioFeatures.tempo, unit: ' BPM' },
            ].map(({ label, desc, value, unit }) => (
              <div key={label}>
                <div className="text-xs text-muted-foreground">{desc}</div>
                <div className="font-semibold">{label}</div>
                <div className="text-xl font-bold text-primary mt-0.5">{value}{unit}</div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {/* Playback Controls */}
      <Card className="p-6">
        <div className="space-y-4">
          {/* Progress Bar */}
          <div className="space-y-2">
            <div
              className="relative h-2 bg-muted rounded-full overflow-hidden cursor-pointer"
              onClick={handleSeek}
            >
              <div
                className="absolute left-0 top-0 h-full bg-primary transition-none rounded-full"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>{formatTime(currentTime)}</span>
              <span>{duration > 0 ? formatTime(duration) : (track.previewUrl ? '0:30' : '--:--')}</span>
            </div>
          </div>

          {/* Main Controls */}
          <div className="flex items-center justify-center gap-4">
            <Button variant="ghost" size="icon">
              <Shuffle className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon" onClick={onPrevious}>
              <SkipBack className="w-5 h-5" />
            </Button>
            <Button size="icon" className="w-14 h-14 rounded-full" onClick={onPlayPause}>
              {isPlaying ? (
                <Pause className="w-6 h-6" />
              ) : (
                <Play className="w-6 h-6 ml-0.5" />
              )}
            </Button>
            <Button variant="ghost" size="icon" onClick={onNext}>
              <SkipForward className="w-5 h-5" />
            </Button>
            <Button variant="ghost" size="icon">
              <Repeat className="w-5 h-5" />
            </Button>
          </div>

          {/* Volume Control */}
          <div className="flex items-center gap-3">
            <Volume2 className="w-5 h-5 text-muted-foreground" />
            <Progress value={70} className="flex-1 h-2" />
          </div>
        </div>
      </Card>
    </div>
  );
}
