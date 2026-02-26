import type {
  MoodAnalyzeResponse,
  MoodAnalysis,
  MoodContext,
  ApiTrack,
  RecommendationRequest,
  RecommendationResponse,
  DeezerPreview,
  DeezerSearchResult,
} from './types';
import type { Track } from '../app/components/TrackCard';

const API_BASE = '/api/v1';

// Placeholder images per mood/genre for when Deezer has no cover art
const PLACEHOLDER_IMAGE =
  'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=400&h=400&fit=crop';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

// Map API emotion label → frontend2 mood button id
export const EMOTION_TO_MOOD: Record<string, string> = {
  joy: 'happy',
  happiness: 'happy',
  happy: 'happy',
  sadness: 'sad',
  sad: 'sad',
  fear: 'sad',
  anger: 'energetic',
  disgust: 'neutral',
  surprise: 'neutral',
  neutral: 'neutral',
  energetic: 'energetic',
  calm: 'calm',
  relaxed: 'calm',
  romantic: 'romantic',
  focused: 'focused',
};

// Map API track + optional Deezer preview to frontend2 Track type
export function mapApiTrack(apiTrack: ApiTrack, deezer?: DeezerPreview): Track {
  const af = apiTrack.audio_features ?? {};
  const score = apiTrack.score ?? 0.8;

  const reason =
    apiTrack.detailed_explanation?.summary ||
    apiTrack.explanation ||
    'Recommended based on your mood and preferences';

  const imageUrl =
    deezer?.cover_medium ||
    deezer?.cover_small ||
    PLACEHOLDER_IMAGE;

  return {
    id: apiTrack.track_id ?? `${apiTrack.name}-${apiTrack.artist}`,
    title: apiTrack.name,
    artist: apiTrack.artist,
    album: apiTrack.album ?? '',
    imageUrl,
    matchScore: Math.round(score * 100),
    audioFeatures: {
      valence: Math.round((af.valence ?? 0.5) * 100),
      energy: Math.round((af.energy ?? 0.5) * 100),
      danceability: Math.round((af.danceability ?? 0.5) * 100),
      tempo: Math.round(af.tempo ?? 120),
    },
    reason,
    previewUrl: deezer?.preview_url,
  };
}

// Analyze free-text mood
export async function analyzeMood(text: string): Promise<MoodAnalysis> {
  const data = await apiFetch<MoodAnalyzeResponse>('/mood/analyze', {
    method: 'POST',
    body: JSON.stringify({ text, include_context: true }),
  });
  return data.mood_analysis;
}

// Get mood-based recommendations (simple path)
export async function getMoodRecommendations(
  mood: string,
  limit = 12,
  context?: MoodContext,
): Promise<ApiTrack[]> {
  const data = await apiFetch<{ status: string; recommendations: ApiTrack[] }>(
    '/mood/recommend',
    {
      method: 'POST',
      body: JSON.stringify({ mood, limit, context }),
    },
  );
  return data.recommendations;
}

// Get hybrid recommendations (seed tracks, context, etc.)
export async function getRecommendations(
  request: RecommendationRequest,
): Promise<RecommendationResponse> {
  return apiFetch<RecommendationResponse>('/recommend', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

// Search tracks with Deezer preview URLs (for seed track search)
export async function searchTracksWithPreview(
  query: string,
  limit = 6,
): Promise<DeezerSearchResult[]> {
  const data = await apiFetch<{ status: string; results: DeezerSearchResult[] }>(
    `/tracks/preview/search?q=${encodeURIComponent(query)}&limit=${limit}`,
  );
  return data.results ?? [];
}

// Fetch Deezer preview for a single track
export async function getTrackPreview(
  artist: string,
  track: string,
): Promise<DeezerPreview | null> {
  try {
    const data = await apiFetch<{ status: string; preview: DeezerPreview }>(
      `/tracks/preview?artist=${encodeURIComponent(artist)}&track=${encodeURIComponent(track)}`,
    );
    return data.preview ?? null;
  } catch {
    return null;
  }
}

// Enrich a list of API tracks with Deezer previews (best-effort, parallel)
export async function enrichWithPreviews(apiTracks: ApiTrack[]): Promise<Track[]> {
  const previews = await Promise.all(
    apiTracks.map((t) => getTrackPreview(t.artist, t.name)),
  );
  return apiTracks.map((t, i) => mapApiTrack(t, previews[i] ?? undefined));
}
