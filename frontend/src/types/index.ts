// API Response Types

export interface ApiResponse<T> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
}

// Mood Analysis
export interface MoodAnalysis {
  primary_emotion: string;
  confidence: number;
  valence: number;
  arousal: number;
  all_emotions: Record<string, number>;
  context?: {
    time_of_day?: string;
    activity?: string;
    weather?: string;
    detected_from_text?: Record<string, boolean>;
  };
  context_adjustment?: {
    valence_delta: number;
    arousal_delta: number;
  };
}

export interface MoodAnalyzeResponse {
  status: string;
  mood_analysis: MoodAnalysis;
}

// Audio Features
export interface AudioFeatures {
  danceability?: number;
  energy?: number;
  valence?: number;
  tempo?: number;
  acousticness?: number;
  instrumentalness?: number;
  speechiness?: number;
  liveness?: number;
  loudness?: number;
}

// Track Types
export interface Track {
  name: string;
  artist: string;
  track_id?: string;
  album?: string;
  source?: string;
  score?: number;
  audio_features?: AudioFeatures;
  explanation?: string;
  detailed_explanation?: DetailedExplanation;
}

export interface TrackWithPreview extends Track {
  deezer_id?: number;
  preview_url?: string;
  cover_small?: string;
  cover_medium?: string;
  cover_large?: string;
  duration?: number;
}

export interface DetailedExplanation {
  track_id: string;
  reason: string;
  confidence: number;
  summary: string;
  details: string[];
  model_contributions: Record<string, number>;
  context_factors: string[];
  top_features?: {
    feature: string;
    description: string;
    contribution: number;
  }[];
}

// Recommendation Types
export interface RecommendationRequest {
  user_id?: string;
  seed_tracks?: { name: string; artist: string }[];
  mood?: string;
  context?: {
    time_of_day?: string;
    activity?: string;
    weather?: string;
  };
  limit?: number;
  include_explanation?: boolean;
  diversity_factor?: number;
  serendipity_factor?: number;
}

export interface RecommendationResponse {
  status: string;
  recommendations: Track[];
  metadata: {
    count: number;
    seed_tracks_provided: number;
    mood?: string;
    context?: Record<string, string>;
    sources: string[];
    explanations_included: boolean;
  };
}

// A/B Testing Types
export interface Experiment {
  name: string;
  description: string;
  status: 'draft' | 'running' | 'paused' | 'completed';
  variants: string[];
  created_at: string;
}

export interface ExperimentVariant {
  name: string;
  weight: number;
  config: Record<string, unknown>;
  metrics?: Record<string, MetricStats>;
}

export interface MetricStats {
  count: number;
  mean: number;
  std: number;
  min: number;
  max: number;
}

export interface ExperimentResults {
  experiment: string;
  status: string;
  duration_hours?: number;
  variants: Record<string, {
    weight: number;
    config: Record<string, unknown>;
    metrics: Record<string, MetricStats>;
  }>;
}

export interface VariantAssignment {
  experiment: string;
  user_id: string;
  variant: {
    name: string;
    config: Record<string, unknown>;
  };
}

// Admin Types
export interface AdminStats {
  models: {
    content_based: ModelInfo;
    collaborative: ModelInfo;
  };
  experiments: {
    name: string;
    status: string;
    variants: number;
    total_observations: number;
  }[];
  feedback: {
    total: number;
    by_type: Record<string, number>;
  };
  generated_at: string;
}

export interface ModelInfo {
  loaded: boolean;
  n_tracks?: number;
  n_users?: number;
  n_neighbors?: number;
  n_factors?: number;
  version?: string;
  trained_at?: string;
}

export interface FeedbackEntry {
  timestamp: string;
  user_id: string;
  track_id: string;
  feedback_type: string;
  value: number;
}

export interface SystemHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  components: Record<string, {
    status: string;
    loaded?: boolean;
    info?: ModelInfo;
    experiments_count?: number;
  }>;
  checked_at: string;
}

// Auth Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  status: string;
  access_token: string;
  token_type: string;
}

// Deezer/Preview Types
export interface DeezerTrack {
  deezer_id: number;
  title: string;
  title_short?: string;
  artist: string;
  artist_id?: number;
  album?: string;
  album_id?: number;
  duration: number;
  preview_url: string;
  cover_small?: string;
  cover_medium?: string;
  cover_large?: string;
  explicit?: boolean;
  rank?: number;
}

// Context Options
export const TIME_OF_DAY_OPTIONS = ['morning', 'afternoon', 'evening', 'night'] as const;
export const ACTIVITY_OPTIONS = ['workout', 'work', 'relaxation', 'party', 'commute', 'focus', 'social'] as const;
export const WEATHER_OPTIONS = ['sunny', 'rainy', 'cloudy', 'cold', 'hot'] as const;

export type TimeOfDay = typeof TIME_OF_DAY_OPTIONS[number];
export type Activity = typeof ACTIVITY_OPTIONS[number];
export type Weather = typeof WEATHER_OPTIONS[number];

// Emotion Colors
export const EMOTION_COLORS: Record<string, string> = {
  joy: '#fbbf24',
  happiness: '#fbbf24',
  happy: '#fbbf24',
  sadness: '#60a5fa',
  sad: '#60a5fa',
  anger: '#ef4444',
  angry: '#ef4444',
  fear: '#a855f7',
  surprise: '#f472b6',
  disgust: '#22c55e',
  neutral: '#94a3b8',
};
