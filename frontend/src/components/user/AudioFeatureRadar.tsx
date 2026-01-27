import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { AudioFeatures } from "../../types";

interface AudioFeatureRadarProps {
  features: AudioFeatures;
  size?: "sm" | "md" | "lg";
}

const FEATURE_LABELS: Record<string, string> = {
  danceability: "Danceable",
  energy: "Energy",
  valence: "Positivity",
  acousticness: "Acoustic",
  instrumentalness: "Instrumental",
  speechiness: "Speechy",
  liveness: "Live",
};

export default function AudioFeatureRadar({
  features,
  size = "md",
}: AudioFeatureRadarProps) {
  const sizes = {
    sm: 120,
    md: 200,
    lg: 280,
  };

  const data = Object.entries(features)
    .filter(([key]) => key in FEATURE_LABELS)
    .map(([key, value]) => ({
      feature: FEATURE_LABELS[key] || key,
      value: (value || 0) * 100,
      fullMark: 100,
    }));

  if (data.length === 0) {
    return (
      <div
        className="flex items-center justify-center text-[var(--text-muted)] text-sm"
        style={{ height: sizes[size] }}
      >
        No audio features available
      </div>
    );
  }

  return (
    <div style={{ width: sizes[size], height: sizes[size] }}>
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis
            dataKey="feature"
            tick={{
              fill: "var(--text-muted)",
              fontSize: size === "sm" ? 8 : 10,
            }}
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
            stroke="var(--primary)"
            fill="var(--primary)"
            fillOpacity={0.3}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--surface)",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              color: "white",
            }}
            formatter={(value) => [
              `${Number(value ?? 0).toFixed(0)}%`,
              "Value",
            ]}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
