import { useState } from "react";
import { Play, Pause, Heart, Info, ChevronDown, ChevronUp } from "lucide-react";
import type { Track, TrackWithPreview } from "../../types";
import AudioFeatureRadar from "./AudioFeatureRadar";

interface RecommendationCardProps {
  track: Track | TrackWithPreview;
  previewUrl?: string;
  coverUrl?: string;
  isPlaying?: boolean;
  onPlayClick?: () => void;
  onSaveClick?: () => void;
  rank?: number;
}

export default function RecommendationCard({
  track,
  previewUrl,
  coverUrl,
  isPlaying = false,
  onPlayClick,
  onSaveClick,
  rank,
}: RecommendationCardProps) {
  const [showDetails, setShowDetails] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  const handleSave = () => {
    setIsSaved(!isSaved);
    onSaveClick?.();
  };

  const explanation = track.detailed_explanation || null;
  const score = track.score ? (track.score * 100).toFixed(0) : null;

  return (
    <div className="glass rounded-xl overflow-hidden hover:border-[var(--primary)]/30 transition-all">
      <div className="flex items-center gap-4 p-4">
        {/* Rank */}
        {rank && (
          <div className="w-8 h-8 rounded-full bg-[var(--surface-light)] flex items-center justify-center text-sm font-medium text-[var(--text-muted)]">
            {rank}
          </div>
        )}

        {/* Album Cover / Play Button */}
        <div className="relative w-14 h-14 rounded-lg overflow-hidden flex-shrink-0 group">
          {coverUrl ? (
            <img
              src={coverUrl}
              alt={track.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-gradient-to-br from-[var(--primary)] to-[var(--secondary)] flex items-center justify-center">
              <span className="text-xl font-bold text-white">
                {track.name.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
          {previewUrl && (
            <button
              onClick={onPlayClick}
              className={`
                absolute inset-0 flex items-center justify-center bg-black/50 transition-opacity
                ${isPlaying ? "opacity-100" : "opacity-0 group-hover:opacity-100"}
              `}
            >
              {isPlaying ? (
                <Pause className="w-6 h-6 text-white" />
              ) : (
                <Play className="w-6 h-6 text-white ml-1" />
              )}
            </button>
          )}
          {isPlaying && (
            <div className="absolute bottom-1 left-1/2 -translate-x-1/2 flex gap-0.5">
              {[...Array(3)].map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-[var(--primary)] rounded-full animate-pulse"
                  style={{
                    height: `${6 + Math.random() * 6}px`,
                    animationDelay: `${i * 0.15}s`,
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Track Info */}
        <div className="flex-1 min-w-0">
          <h4 className="font-medium text-white truncate">{track.name}</h4>
          <p className="text-sm text-[var(--text-muted)] truncate">
            {track.artist}
          </p>
          {track.source && (
            <span className="inline-block mt-1 px-2 py-0.5 text-xs rounded-full bg-[var(--surface-light)] text-[var(--text-muted)]">
              {track.source}
            </span>
          )}
        </div>

        {/* Score */}
        {score && (
          <div className="text-right">
            <div className="text-lg font-bold text-[var(--primary)]">
              {score}%
            </div>
            <div className="text-xs text-[var(--text-muted)]">match</div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            className={`p-2 rounded-full transition-colors ${
              isSaved
                ? "text-[var(--accent)] bg-[var(--accent)]/20"
                : "text-[var(--text-muted)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/10"
            }`}
          >
            <Heart className={`w-5 h-5 ${isSaved ? "fill-current" : ""}`} />
          </button>
          {(explanation || track.audio_features) && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="p-2 rounded-full text-[var(--text-muted)] hover:text-white hover:bg-white/10 transition-colors"
            >
              {showDetails ? (
                <ChevronUp className="w-5 h-5" />
              ) : (
                <ChevronDown className="w-5 h-5" />
              )}
            </button>
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {showDetails && (
        <div className="px-4 pb-4 pt-2 border-t border-white/5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Explanation */}
            {explanation && (
              <div>
                <h5 className="text-sm font-medium text-white mb-2 flex items-center gap-2">
                  <Info className="w-4 h-4 text-[var(--primary)]" />
                  Why this track?
                </h5>
                <p className="text-sm text-[var(--text-muted)] mb-3">
                  {explanation.summary}
                </p>

                {explanation.details.length > 0 && (
                  <ul className="space-y-1 mb-3">
                    {explanation.details.map((detail, i) => (
                      <li
                        key={i}
                        className="text-xs text-[var(--text-muted)] flex items-start gap-2"
                      >
                        <span className="text-[var(--primary)]">•</span>
                        {detail}
                      </li>
                    ))}
                  </ul>
                )}

                {explanation.context_factors.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {explanation.context_factors.map((factor, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-xs rounded-full bg-[var(--secondary)]/20 text-[var(--secondary)]"
                      >
                        {factor}
                      </span>
                    ))}
                  </div>
                )}

                {/* Model Contributions */}
                {explanation.model_contributions && (
                  <div className="mt-3">
                    <p className="text-xs text-[var(--text-muted)] mb-1">
                      Model contributions:
                    </p>
                    <div className="flex gap-2">
                      {Object.entries(explanation.model_contributions).map(
                        ([model, contribution]) => (
                          <div
                            key={model}
                            className="flex items-center gap-1 text-xs"
                          >
                            <div
                              className="w-2 h-2 rounded-full"
                              style={{
                                backgroundColor:
                                  model === "content"
                                    ? "var(--primary)"
                                    : model === "collaborative"
                                      ? "var(--secondary)"
                                      : "var(--accent)",
                              }}
                            />
                            <span className="text-[var(--text-muted)] capitalize">
                              {model}:{" "}
                              {((contribution as number) * 100).toFixed(0)}%
                            </span>
                          </div>
                        ),
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Audio Features */}
            {track.audio_features && (
              <div className="flex flex-col items-center">
                <h5 className="text-sm font-medium text-white mb-2 self-start">
                  Audio Features
                </h5>
                <AudioFeatureRadar features={track.audio_features} size="md" />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
