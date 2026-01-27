import axios from "axios";
import type { AxiosInstance, AxiosError } from "axios";
import type {
  MoodAnalyzeResponse,
  RecommendationRequest,
  RecommendationResponse,
  Track,
  DeezerTrack,
  Experiment,
  ExperimentResults,
  VariantAssignment,
  AdminStats,
  FeedbackEntry,
  SystemHealth,
  LoginResponse,
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

class ApiService {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Load token from localStorage
    this.token = localStorage.getItem("admin_token");

    // Add auth interceptor
    this.client.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`;
      }
      return config;
    });

    // Handle errors
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          this.clearToken();
        }
        return Promise.reject(error);
      },
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem("admin_token", token);
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem("admin_token");
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  // Auth endpoints
  async login(username: string, password: string): Promise<LoginResponse> {
    const response = await this.client.post<LoginResponse>("/auth/login", {
      username,
      password,
    });
    if (response.data.access_token) {
      this.setToken(response.data.access_token);
    }
    return response.data;
  }

  async verifyToken(): Promise<boolean> {
    try {
      await this.client.get("/auth/verify");
      return true;
    } catch {
      this.clearToken();
      return false;
    }
  }

  logout() {
    this.clearToken();
  }

  // Mood endpoints
  async analyzeMood(
    text: string,
    includeContext = true,
  ): Promise<MoodAnalyzeResponse> {
    const response = await this.client.post<MoodAnalyzeResponse>(
      "/mood/analyze",
      {
        text,
        include_context: includeContext,
      },
    );
    return response.data;
  }

  async getMoodRecommendations(
    mood: string,
    limit = 10,
    context?: { time_of_day?: string; activity?: string; weather?: string },
  ): Promise<Track[]> {
    const response = await this.client.post<{ recommendations: Track[] }>(
      "/mood/recommend",
      {
        mood,
        limit,
        context,
      },
    );
    return response.data.recommendations;
  }

  // Recommendation endpoints
  async getRecommendations(
    request: RecommendationRequest,
  ): Promise<RecommendationResponse> {
    const response = await this.client.post<RecommendationResponse>(
      "/recommend",
      request,
    );
    return response.data;
  }

  async getSimilarTracks(
    artist: string,
    track: string,
    limit = 10,
  ): Promise<Track[]> {
    const response = await this.client.post<{ similar_tracks: Track[] }>(
      "/recommend/similar",
      {
        artist,
        track,
        limit,
      },
    );
    return response.data.similar_tracks;
  }

  // Track endpoints
  async searchTracks(
    query: string,
    limit = 10,
    source = "both",
  ): Promise<Track[]> {
    const response = await this.client.get<{ results: Track[] }>(
      "/tracks/search",
      {
        params: { q: query, limit, source },
      },
    );
    return response.data.results;
  }

  async getTrackPreview(
    artist: string,
    track: string,
  ): Promise<DeezerTrack | null> {
    try {
      const response = await this.client.get<{ preview: DeezerTrack }>(
        "/tracks/preview",
        {
          params: { artist, track },
        },
      );
      return response.data.preview;
    } catch {
      return null;
    }
  }

  async searchTracksWithPreview(
    query: string,
    limit = 10,
  ): Promise<DeezerTrack[]> {
    const response = await this.client.get<{ results: DeezerTrack[] }>(
      "/tracks/preview/search",
      {
        params: { q: query, limit },
      },
    );
    return response.data.results;
  }

  async getTrackFeatures(
    trackId: string,
  ): Promise<{ audio_features: Record<string, number> } | null> {
    try {
      const response = await this.client.get(`/tracks/${trackId}/features`);
      return response.data;
    } catch {
      return null;
    }
  }

  // Feedback endpoint
  async recordFeedback(
    userId: string,
    trackId: string,
    feedbackType: "click" | "play" | "skip" | "save" | "listen_time",
    value = 1.0,
  ): Promise<void> {
    await this.client.post("/feedback", {
      user_id: userId,
      track_id: trackId,
      feedback_type: feedbackType,
      value,
    });
  }

  // Experiment endpoints (public)
  async getExperiments(): Promise<Experiment[]> {
    const response = await this.client.get<{ experiments: Experiment[] }>(
      "/experiments",
    );
    return response.data.experiments;
  }

  async getExperiment(name: string): Promise<ExperimentResults> {
    const response = await this.client.get<ExperimentResults>(
      `/experiments/${name}`,
    );
    return response.data;
  }

  async getVariantAssignment(
    experimentName: string,
    userId: string,
  ): Promise<VariantAssignment> {
    const response = await this.client.get<VariantAssignment>(
      `/experiments/${experimentName}/variant`,
      { params: { user_id: userId } },
    );
    return response.data;
  }

  // Admin endpoints (protected)
  async getAdminStats(): Promise<AdminStats> {
    const response = await this.client.get<AdminStats>("/admin/stats");
    return response.data;
  }

  async getAdminFeedbackLog(
    limit = 50,
    feedbackType?: string,
  ): Promise<FeedbackEntry[]> {
    const response = await this.client.get<{ entries: FeedbackEntry[] }>(
      "/admin/feedback",
      {
        params: { limit, feedback_type: feedbackType },
      },
    );
    return response.data.entries;
  }

  async getAdminExperimentDetail(name: string): Promise<{
    experiment: ExperimentResults;
    comparison: Record<
      string,
      Record<string, { mean: number; std: number; count: number }>
    >;
  }> {
    const response = await this.client.get(`/admin/experiments/${name}`);
    return response.data;
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.client.get<SystemHealth>("/admin/health");
    return response.data;
  }
}

export const api = new ApiService();
export default api;
