import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, Music2, Sliders } from "lucide-react";
import Layout from "../components/common/Layout";
import Card from "../components/common/Card";
import Button from "../components/common/Button";
import MoodInput from "../components/user/MoodInput";
import ContextSelector from "../components/user/ContextSelector";
import EmotionDisplay from "../components/user/EmotionDisplay";
import TrackSearch, { SelectedTracks } from "../components/user/TrackSearch";
import type { MoodAnalysis, TimeOfDay, Activity, Weather } from "../types";
import api from "../services/api";

export default function Home() {
  const navigate = useNavigate();

  // Mood state
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [moodAnalysis, setMoodAnalysis] = useState<MoodAnalysis | null>(null);

  // Context state
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay | undefined>();
  const [activity, setActivity] = useState<Activity | undefined>();
  const [weather, setWeather] = useState<Weather | undefined>();
  const [showContext, setShowContext] = useState(false);

  // Seed tracks state
  const [seedTracks, setSeedTracks] = useState<
    { name: string; artist: string }[]
  >([]);
  const [showSeedTracks, setShowSeedTracks] = useState(false);

  // Settings
  const [diversityFactor, setDiversityFactor] = useState(0.3);
  const [serendipityFactor, setSerendipityFactor] = useState(0.1);
  const [showSettings, setShowSettings] = useState(false);

  const handleAnalyze = async (text: string) => {
    setIsAnalyzing(true);

    try {
      const response = await api.analyzeMood(text, true);
      setMoodAnalysis(response.mood_analysis);

      // Auto-detect context from analysis if present
      if (response.mood_analysis.context) {
        if (response.mood_analysis.context.time_of_day) {
          setTimeOfDay(response.mood_analysis.context.time_of_day as TimeOfDay);
        }
        if (response.mood_analysis.context.activity) {
          setActivity(response.mood_analysis.context.activity as Activity);
        }
        if (response.mood_analysis.context.weather) {
          setWeather(response.mood_analysis.context.weather as Weather);
        }
      }
    } catch (error) {
      console.error("Analysis error:", error);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGetRecommendations = () => {
    // Store state and navigate to recommendations page
    const params = new URLSearchParams();

    if (moodAnalysis) {
      params.set("mood", moodAnalysis.primary_emotion);
    }
    if (timeOfDay) params.set("time", timeOfDay);
    if (activity) params.set("activity", activity);
    if (weather) params.set("weather", weather);
    if (seedTracks.length > 0) {
      params.set("seeds", JSON.stringify(seedTracks));
    }
    params.set("diversity", diversityFactor.toString());
    params.set("serendipity", serendipityFactor.toString());

    navigate(`/recommendations?${params.toString()}`);
  };

  const handleAddSeedTrack = (track: { name: string; artist: string }) => {
    setSeedTracks([...seedTracks, track]);
  };

  const handleRemoveSeedTrack = (index: number) => {
    setSeedTracks(seedTracks.filter((_, i) => i !== index));
  };

  return (
    <Layout>
      <div className="min-h-screen py-12 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Hero Section */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              <span className="gradient-text">Music for Your Mood</span>
            </h1>
            <p className="text-lg text-[var(--text-muted)] max-w-2xl mx-auto">
              Tell us how you're feeling, and we'll find the perfect tracks for
              you. Powered by AI-driven mood analysis and personalized
              recommendations.
            </p>
          </div>

          {/* Mood Input */}
          <Card className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-[var(--primary)]" />
              <h2 className="text-lg font-semibold text-white">
                How are you feeling?
              </h2>
            </div>
            <MoodInput onAnalyze={handleAnalyze} isLoading={isAnalyzing} />
          </Card>

          {/* Mood Analysis Result */}
          {moodAnalysis && (
            <div className="mb-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <EmotionDisplay analysis={moodAnalysis} />
            </div>
          )}

          {/* Optional Sections */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {/* Seed Tracks */}
            <Card
              hover
              onClick={() => setShowSeedTracks(!showSeedTracks)}
              className={showSeedTracks ? "border-[var(--primary)]/50" : ""}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--secondary)]/20 flex items-center justify-center">
                    <Music2 className="w-5 h-5 text-[var(--secondary)]" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">Seed Tracks</h3>
                    <p className="text-sm text-[var(--text-muted)]">
                      {seedTracks.length > 0
                        ? `${seedTracks.length} track${seedTracks.length > 1 ? "s" : ""} selected`
                        : "Optional: Add tracks you like"}
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Context */}
            <Card
              hover
              onClick={() => setShowContext(!showContext)}
              className={showContext ? "border-[var(--primary)]/50" : ""}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-[var(--accent)]/20 flex items-center justify-center">
                    <Sliders className="w-5 h-5 text-[var(--accent)]" />
                  </div>
                  <div>
                    <h3 className="font-medium text-white">
                      Context & Settings
                    </h3>
                    <p className="text-sm text-[var(--text-muted)]">
                      {timeOfDay || activity || weather
                        ? "Context configured"
                        : "Time, activity, weather"}
                    </p>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Expanded Seed Tracks */}
          {showSeedTracks && (
            <Card className="mb-8 animate-in fade-in slide-in-from-top-2 duration-300">
              <h3 className="text-lg font-semibold text-white mb-4">
                Add Seed Tracks
              </h3>
              <TrackSearch
                onSelect={handleAddSeedTrack}
                selectedTracks={seedTracks}
                maxTracks={3}
              />
              <SelectedTracks
                tracks={seedTracks}
                onRemove={handleRemoveSeedTrack}
              />
            </Card>
          )}

          {/* Expanded Context */}
          {showContext && (
            <Card className="mb-8 animate-in fade-in slide-in-from-top-2 duration-300">
              <h3 className="text-lg font-semibold text-white mb-4">
                Context & Settings
              </h3>

              <ContextSelector
                timeOfDay={timeOfDay}
                activity={activity}
                weather={weather}
                onTimeChange={setTimeOfDay}
                onActivityChange={setActivity}
                onWeatherChange={setWeather}
              />

              <div className="mt-6 pt-6 border-t border-white/10">
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="text-sm text-[var(--text-muted)] hover:text-white transition-colors"
                >
                  {showSettings ? "Hide" : "Show"} advanced settings
                </button>

                {showSettings && (
                  <div className="mt-4 space-y-4">
                    <div>
                      <div className="flex justify-between mb-2">
                        <label className="text-sm text-[var(--text-muted)]">
                          Diversity: {(diversityFactor * 100).toFixed(0)}%
                        </label>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={diversityFactor}
                        onChange={(e) =>
                          setDiversityFactor(parseFloat(e.target.value))
                        }
                        className="w-full h-2 bg-[var(--surface-light)] rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-[var(--primary)] [&::-webkit-slider-thumb]:rounded-full"
                      />
                      <p className="text-xs text-[var(--text-muted)] mt-1">
                        Higher diversity = more varied recommendations
                      </p>
                    </div>

                    <div>
                      <div className="flex justify-between mb-2">
                        <label className="text-sm text-[var(--text-muted)]">
                          Serendipity: {(serendipityFactor * 100).toFixed(0)}%
                        </label>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="0.5"
                        step="0.05"
                        value={serendipityFactor}
                        onChange={(e) =>
                          setSerendipityFactor(parseFloat(e.target.value))
                        }
                        className="w-full h-2 bg-[var(--surface-light)] rounded-full appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:bg-[var(--secondary)] [&::-webkit-slider-thumb]:rounded-full"
                      />
                      <p className="text-xs text-[var(--text-muted)] mt-1">
                        Higher serendipity = more surprising discoveries
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </Card>
          )}

          {/* Get Recommendations Button */}
          <div className="flex justify-center">
            <Button
              size="lg"
              onClick={handleGetRecommendations}
              disabled={!moodAnalysis && seedTracks.length === 0}
              leftIcon={<Sparkles className="w-5 h-5" />}
            >
              Get Recommendations
            </Button>
          </div>

          {!moodAnalysis && seedTracks.length === 0 && (
            <p className="text-center text-sm text-[var(--text-muted)] mt-4">
              Analyze your mood or add seed tracks to get started
            </p>
          )}
        </div>
      </div>
    </Layout>
  );
}
