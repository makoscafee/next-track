import type { MoodAnalysis } from "../../types";
import { EMOTION_COLORS } from "../../types";
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
} from "recharts";

interface EmotionDisplayProps {
  analysis: MoodAnalysis;
}

export default function EmotionDisplay({ analysis }: EmotionDisplayProps) {
  const primaryColor =
    EMOTION_COLORS[analysis.primary_emotion.toLowerCase()] || "#8b5cf6";

  // Prepare data for radar chart
  const emotionData = Object.entries(analysis.all_emotions)
    .map(([emotion, value]) => ({
      emotion: emotion.charAt(0).toUpperCase() + emotion.slice(1),
      value: value * 100,
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 7); // Top 7 emotions

  // Valence-Arousal quadrant position
  const quadrant = getQuadrant(analysis.valence, analysis.arousal);

  return (
    <div className="glass rounded-2xl p-6">
      <div className="flex items-start justify-between mb-6">
        <div>
          <h3 className="text-sm text-[var(--text-muted)] mb-1">
            Detected Emotion
          </h3>
          <div className="flex items-center gap-3">
            <span
              className="text-3xl font-bold capitalize"
              style={{ color: primaryColor }}
            >
              {analysis.primary_emotion}
            </span>
            <span className="px-2 py-1 text-sm rounded-full bg-white/10 text-[var(--text-muted)]">
              {(analysis.confidence * 100).toFixed(1)}% confident
            </span>
          </div>
        </div>
        <div className="text-right">
          <span className="text-sm text-[var(--text-muted)]">{quadrant}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Emotion Radar Chart */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={emotionData}>
              <PolarGrid stroke="rgba(255,255,255,0.1)" />
              <PolarAngleAxis
                dataKey="emotion"
                tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              />
              <PolarRadiusAxis
                angle={30}
                domain={[0, 100]}
                tick={{ fill: "var(--text-muted)", fontSize: 10 }}
              />
              <Radar
                name="Emotion"
                dataKey="value"
                stroke={primaryColor}
                fill={primaryColor}
                fillOpacity={0.3}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Valence-Arousal Display */}
        <div className="space-y-4">
          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-[var(--text-muted)]">
                Valence (Positivity)
              </span>
              <span className="text-sm font-medium">
                {(analysis.valence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-2 bg-[var(--surface-light)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${analysis.valence * 100}%`,
                  background: `linear-gradient(90deg, #ef4444, #fbbf24, #22c55e)`,
                }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-[var(--text-muted)]">
              <span>Negative</span>
              <span>Positive</span>
            </div>
          </div>

          <div>
            <div className="flex justify-between mb-1">
              <span className="text-sm text-[var(--text-muted)]">
                Arousal (Energy)
              </span>
              <span className="text-sm font-medium">
                {(analysis.arousal * 100).toFixed(0)}%
              </span>
            </div>
            <div className="h-2 bg-[var(--surface-light)] rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${analysis.arousal * 100}%`,
                  background: `linear-gradient(90deg, #60a5fa, #8b5cf6, #ef4444)`,
                }}
              />
            </div>
            <div className="flex justify-between mt-1 text-xs text-[var(--text-muted)]">
              <span>Calm</span>
              <span>Energetic</span>
            </div>
          </div>

          {/* Context Display */}
          {analysis.context && Object.keys(analysis.context).length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/10">
              <h4 className="text-sm text-[var(--text-muted)] mb-2">
                Detected Context
              </h4>
              <div className="flex flex-wrap gap-2">
                {analysis.context.time_of_day && (
                  <span className="px-2 py-1 text-xs rounded-full bg-[var(--primary)]/20 text-[var(--primary)]">
                    {analysis.context.time_of_day}
                  </span>
                )}
                {analysis.context.activity && (
                  <span className="px-2 py-1 text-xs rounded-full bg-[var(--secondary)]/20 text-[var(--secondary)]">
                    {analysis.context.activity}
                  </span>
                )}
                {analysis.context.weather && (
                  <span className="px-2 py-1 text-xs rounded-full bg-[var(--accent)]/20 text-[var(--accent)]">
                    {analysis.context.weather}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function getQuadrant(valence: number, arousal: number): string {
  if (valence >= 0.5 && arousal >= 0.5) return "High Energy, Positive";
  if (valence >= 0.5 && arousal < 0.5) return "Low Energy, Positive";
  if (valence < 0.5 && arousal >= 0.5) return "High Energy, Negative";
  return "Low Energy, Negative";
}
