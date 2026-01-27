import { useState, useEffect, useRef, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { ArrowLeft, RefreshCw, Volume2 } from "lucide-react";
import Layout from "../components/common/Layout";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import RecommendationCard from "../components/user/RecommendationCard";
import AudioPlayer from "../components/user/AudioPlayer";
import type { Track, DeezerTrack, RecommendationRequest } from "../types";
import api from "../services/api";

// Generate a unique user ID for this session (for A/B testing)
const getUserId = () => {
  let userId = localStorage.getItem("nexttrack_user_id");
  if (!userId) {
    userId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    localStorage.setItem("nexttrack_user_id", userId);
  }
  return userId;
};

export default function Recommendations() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [recommendations, setRecommendations] = useState<Track[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Audio player state
  const [currentTrack, setCurrentTrack] = useState<Track | null>(null);
  const [currentPreview, setCurrentPreview] = useState<DeezerTrack | null>(
    null,
  );
  const [isPlaying, setIsPlaying] = useState(false);
  const [previewCache, setPreviewCache] = useState<Record<string, DeezerTrack>>(
    {},
  );

  const userId = useRef(getUserId());

  const fetchRecommendations = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const mood = searchParams.get("mood");
      const time = searchParams.get("time");
      const activity = searchParams.get("activity");
      const weather = searchParams.get("weather");
      const seedsParam = searchParams.get("seeds");
      const diversity = parseFloat(searchParams.get("diversity") || "0.3");
      const serendipity = parseFloat(searchParams.get("serendipity") || "0.1");

      let seedTracks: { name: string; artist: string }[] = [];
      if (seedsParam) {
        try {
          seedTracks = JSON.parse(seedsParam);
        } catch {
          console.error("Failed to parse seed tracks");
        }
      }

      const request: RecommendationRequest = {
        user_id: userId.current,
        limit: 15,
        include_explanation: true,
        diversity_factor: diversity,
        serendipity_factor: serendipity,
      };

      if (mood) request.mood = mood;
      if (seedTracks.length > 0) request.seed_tracks = seedTracks;

      if (time || activity || weather) {
        request.context = {};
        if (time) request.context.time_of_day = time;
        if (activity) request.context.activity = activity;
        if (weather) request.context.weather = weather;
      }

      const response = await api.getRecommendations(request);
      setRecommendations(response.recommendations);
    } catch (err) {
      console.error("Failed to fetch recommendations:", err);
      setError("Failed to load recommendations. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchRecommendations();
  }, [fetchRecommendations]);

  const handlePlayTrack = async (track: Track) => {
    const cacheKey = `${track.name}-${track.artist}`;

    // Check cache first
    if (previewCache[cacheKey]) {
      setCurrentPreview(previewCache[cacheKey]);
      setCurrentTrack(track);
      setIsPlaying(true);

      // Record click feedback
      api.recordFeedback(userId.current, track.track_id || cacheKey, "click");
      return;
    }

    // Fetch preview from Deezer
    try {
      const preview = await api.getTrackPreview(track.artist, track.name);
      if (preview) {
        setPreviewCache((prev) => ({ ...prev, [cacheKey]: preview }));
        setCurrentPreview(preview);
        setCurrentTrack(track);
        setIsPlaying(true);

        // Record click feedback
        api.recordFeedback(userId.current, track.track_id || cacheKey, "click");
      }
    } catch (err) {
      console.error("Failed to fetch preview:", err);
    }
  };

  const handleTrackPlay = () => {
    setIsPlaying(true);
    if (currentTrack) {
      api.recordFeedback(
        userId.current,
        currentTrack.track_id || currentTrack.name,
        "play",
      );
    }
  };

  const handleTrackPause = () => {
    setIsPlaying(false);
  };

  const handleTrackEnded = () => {
    setIsPlaying(false);
    // Auto-play next track
    if (currentTrack) {
      const currentIndex = recommendations.findIndex(
        (t) => t.name === currentTrack.name && t.artist === currentTrack.artist,
      );
      if (currentIndex < recommendations.length - 1) {
        handlePlayTrack(recommendations[currentIndex + 1]);
      }
    }
  };

  const handleSaveTrack = (track: Track) => {
    api.recordFeedback(userId.current, track.track_id || track.name, "save");
  };

  const mood = searchParams.get("mood");
  const context = {
    time: searchParams.get("time"),
    activity: searchParams.get("activity"),
    weather: searchParams.get("weather"),
  };

  return (
    <Layout>
      <div className="min-h-screen py-8 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                onClick={() => navigate("/")}
                leftIcon={<ArrowLeft className="w-4 h-4" />}
              >
                Back
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-white">
                  Your Recommendations
                </h1>
                <p className="text-sm text-[var(--text-muted)]">
                  {mood && <span className="capitalize">Mood: {mood}</span>}
                  {context.activity && (
                    <span> | Activity: {context.activity}</span>
                  )}
                </p>
              </div>
            </div>
            <Button
              variant="secondary"
              onClick={fetchRecommendations}
              isLoading={isLoading}
              leftIcon={<RefreshCw className="w-4 h-4" />}
            >
              Refresh
            </Button>
          </div>

          {/* Now Playing */}
          {currentPreview && currentTrack && (
            <Card className="mb-6 border-[var(--primary)]/30">
              <div className="flex items-center gap-2 mb-3">
                <Volume2 className="w-4 h-4 text-[var(--primary)]" />
                <span className="text-sm font-medium text-white">
                  Now Playing
                </span>
              </div>
              <AudioPlayer
                previewUrl={currentPreview.preview_url}
                trackName={currentPreview.title}
                artistName={currentPreview.artist}
                coverUrl={currentPreview.cover_medium}
                onPlay={handleTrackPlay}
                onPause={handleTrackPause}
                onEnded={handleTrackEnded}
              />
            </Card>
          )}

          {/* Loading State */}
          {isLoading && (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="w-16 h-16 border-4 border-[var(--primary)] border-t-transparent rounded-full animate-spin mb-4" />
              <p className="text-[var(--text-muted)]">
                Finding the perfect tracks for you...
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !isLoading && (
            <Card className="text-center py-8">
              <p className="text-[var(--error)] mb-4">{error}</p>
              <Button onClick={fetchRecommendations}>Try Again</Button>
            </Card>
          )}

          {/* Recommendations List */}
          {!isLoading && !error && (
            <div className="space-y-4">
              {recommendations.length === 0 ? (
                <Card className="text-center py-8">
                  <p className="text-[var(--text-muted)]">
                    No recommendations found. Try adjusting your criteria.
                  </p>
                  <Button onClick={() => navigate("/")} className="mt-4">
                    Go Back
                  </Button>
                </Card>
              ) : (
                recommendations.map((track, index) => {
                  const cacheKey = `${track.name}-${track.artist}`;
                  const preview = previewCache[cacheKey];
                  const isCurrentlyPlaying =
                    isPlaying &&
                    currentTrack?.name === track.name &&
                    currentTrack?.artist === track.artist;

                  return (
                    <RecommendationCard
                      key={`${track.name}-${track.artist}-${index}`}
                      track={track}
                      previewUrl={preview?.preview_url}
                      coverUrl={preview?.cover_medium}
                      isPlaying={isCurrentlyPlaying}
                      onPlayClick={() => handlePlayTrack(track)}
                      onSaveClick={() => handleSaveTrack(track)}
                      rank={index + 1}
                    />
                  );
                })
              )}
            </div>
          )}

          {/* Info */}
          {!isLoading && recommendations.length > 0 && (
            <p className="text-center text-sm text-[var(--text-muted)] mt-8">
              Showing {recommendations.length} recommendations based on your
              preferences. Click on a track to preview it.
            </p>
          )}
        </div>
      </div>
    </Layout>
  );
}
