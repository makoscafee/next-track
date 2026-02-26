// API response types for the NextTrack backend

export interface MoodContext {
  time_of_day?: string;
  activity?: string;
  weather?: string;
}

export interface MoodAnalysis {
  primary_emotion: string;
  confidence: number;
  valence: number;
  arousal: number;
  all_emotions: Record<string, number>;
  context: MoodContext & {
    detected_from_text?: Record<string, boolean>;
  };
}

export interface MoodAnalyzeResponse {
  status: string;
  mood_analysis: MoodAnalysis;
}

export interface ApiAudioFeatures {
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

export interface ApiTrack {
  name: string;
  artist: string;
  track_id?: string;
  album?: string;
  score?: number;
  source?: string;
  explanation?: string;
  audio_features?: ApiAudioFeatures;
  detailed_explanation?: {
    summary?: string;
    details?: string[];
    context_factors?: string[];
    model_contributions?: Record<string, number>;
  };
}

export interface RecommendationRequest {
  mood?: string;
  seed_tracks?: { name: string; artist: string }[];
  context?: MoodContext;
  limit?: number;
  include_explanation?: boolean;
  diversity_factor?: number;
  serendipity_factor?: number;
  preferred_genres?: string[];
  exclude_explicit?: boolean;
}

export interface RecommendationResponse {
  status: string;
  recommendations: ApiTrack[];
  metadata: {
    count: number;
    mood?: string;
    latency_ms?: number;
  };
}

export interface DeezerPreview {
  deezer_id?: number;
  title?: string;
  artist?: string;
  album?: string;
  preview_url?: string;
  cover_small?: string;
  cover_medium?: string;
  cover_large?: string;
  duration?: number;
}

export interface DeezerSearchResult extends DeezerPreview {
  name?: string;
  artists?: string;
}

// ── Admin Dashboard Types ────────────────────────────────────────────────────

export interface AdminModelInfo {
  loaded: boolean;
  n_tracks?: number;
  n_users?: number;
  version?: string;
  trained_at?: string;
  [k: string]: unknown;
}

export interface AdminStats {
  models: {
    content_based: AdminModelInfo;
    collaborative: AdminModelInfo;
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

export interface AdminHealthComponent {
  status: string;
  loaded?: boolean;
  info?: Record<string, unknown>;
  experiments_count?: number;
}

export interface AdminHealth {
  status: string;
  components: {
    content_based_model: AdminHealthComponent;
    collaborative_model: AdminHealthComponent;
    ab_testing: AdminHealthComponent;
  };
  checked_at: string;
}

export interface FeedbackEntry {
  timestamp: string;
  user_id: string;
  track_id: string;
  feedback_type: string;
  value: number;
}

export interface AdminFeedbackLog {
  entries: FeedbackEntry[];
  count: number;
  total_in_log: number;
}

export interface ExperimentVariantMetric {
  mean: number;
  std: number;
  count: number;
}

export interface AdminExperimentDetail {
  experiment: {
    name: string;
    status: string;
    variants: Record<string, { metrics: Record<string, ExperimentVariantMetric> }>;
  };
  comparison: Record<string, Record<string, ExperimentVariantMetric>>;
  generated_at: string;
}
