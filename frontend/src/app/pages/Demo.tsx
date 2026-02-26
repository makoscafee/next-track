import React, { useState } from 'react';
import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { MoodSelector } from '../components/MoodSelector';
import { PresetPlaylists } from '../components/PresetPlaylists';
import { PlaylistItem } from '../components/PlaylistItem';
import { NowPlaying } from '../components/NowPlaying';
import { Stepper } from '../components/Stepper';
import { MoodTextInput } from '../components/MoodTextInput';
import { ContextSelector } from '../components/ContextSelector';
import { SeedTrackSearch } from '../components/SeedTrackSearch';
import type { SeedTrack } from '../components/SeedTrackSearch';
import type { Track } from '../components/TrackCard';
import type { MoodAnalysis, MoodContext } from '../../services/types';
import {
  getMoodRecommendations,
  getRecommendations,
  enrichWithPreviews,
} from '../../services/api';
import { ArrowLeft, TrendingUp, Sparkles, Music } from 'lucide-react';

const DEMO_STEPS = [
  {
    id: 1,
    label: 'Select Your Mood',
    description: 'Choose an emotion or playlist',
  },
  {
    id: 2,
    label: 'Get Recommendations',
    description: 'AI analyzes your preference',
  },
  {
    id: 3,
    label: 'Enjoy Your Playlist',
    description: 'Listen to perfect matches',
  },
];

export function Demo() {
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [selectedPlaylist, setSelectedPlaylist] = useState<string | null>(null);
  const [showRecommendations, setShowRecommendations] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [recommendations, setRecommendations] = useState<Track[]>([]);
  const [context, setContext] = useState<MoodContext>({});
  const [seedTracks, setSeedTracks] = useState<SeedTrack[]>([]);
  const [moodAnalysis, setMoodAnalysis] = useState<MoodAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [apiLatencyMs, setApiLatencyMs] = useState<number | null>(null);

  // Calculate current step
  const getCurrentStep = () => {
    if (showRecommendations) return 3;
    if (selectedMood && !selectedPlaylist) return 2;
    return 1;
  };

  const handleMoodSelect = (moodId: string) => {
    setSelectedMood(moodId);
    setSelectedPlaylist(null);
    setShowRecommendations(false);
    setCurrentTrackIndex(0);
    setIsPlaying(false);
    setError(null);
  };

  const handleMoodDetected = (moodId: string, analysis: MoodAnalysis) => {
    setMoodAnalysis(analysis);
    setSelectedMood(moodId);
    setSelectedPlaylist(null);
    setShowRecommendations(false);
    setCurrentTrackIndex(0);
    setIsPlaying(false);
    setError(null);
  };

  const fetchRecommendations = async (mood: string) => {
    setIsLoading(true);
    setError(null);
    const t0 = Date.now();
    try {
      let tracks: Track[];
      const hasSeeds = seedTracks.length > 0;
      const hasContext = Object.keys(context).some((k) => context[k as keyof MoodContext]);

      if (hasSeeds || hasContext) {
        const result = await getRecommendations({
          mood,
          seed_tracks: seedTracks.map((t) => ({ name: t.name, artist: t.artist })),
          context: hasContext ? context : undefined,
          limit: 12,
          include_explanation: true,
        });
        tracks = await enrichWithPreviews(result.recommendations);
      } else {
        const raw = await getMoodRecommendations(mood, 12, undefined);
        tracks = await enrichWithPreviews(raw);
      }
      setApiLatencyMs(Date.now() - t0);
      setRecommendations(tracks);
      setShowRecommendations(true);
      setCurrentTrackIndex(0);
      setIsPlaying(true);
      setTimeout(() => {
        document.getElementById('results')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch {
      setError('Failed to get recommendations. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handlePlaylistSelect = (playlistId: string, mood: string) => {
    setSelectedPlaylist(playlistId);
    setSelectedMood(mood);
    fetchRecommendations(mood);
  };

  const handleGetRecommendations = () => {
    if (selectedMood) {
      fetchRecommendations(selectedMood);
    }
  };

  const handleReset = () => {
    setSelectedMood(null);
    setSelectedPlaylist(null);
    setShowRecommendations(false);
    setCurrentTrackIndex(0);
    setIsPlaying(false);
    setRecommendations([]);
    setContext({});
    setSeedTracks([]);
    setMoodAnalysis(null);
    setError(null);
    setApiLatencyMs(null);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleNext = () => {
    if (currentTrackIndex < recommendations.length - 1) {
      setCurrentTrackIndex(currentTrackIndex + 1);
      setIsPlaying(true);
    } else {
      setCurrentTrackIndex(0);
      setIsPlaying(true);
    }
  };

  const handlePrevious = () => {
    if (currentTrackIndex > 0) {
      setCurrentTrackIndex(currentTrackIndex - 1);
      setIsPlaying(true);
    } else {
      setCurrentTrackIndex(recommendations.length - 1);
      setIsPlaying(true);
    }
  };

  const handleTrackSelect = (index: number) => {
    setCurrentTrackIndex(index);
    setIsPlaying(true);
  };

  const currentTrack = recommendations[currentTrackIndex];

  // Confidence from mood analysis or a default
  const confidence = moodAnalysis
    ? Math.round(moodAnalysis.confidence * 100)
    : null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-12">
          <Link to="/" className="inline-flex items-center gap-2 text-white/90 hover:text-white mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            <span className="text-sm">Back to Home</span>
          </Link>

          <div className="text-center">
            <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-sm px-4 py-2 rounded-full mb-4">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-semibold">Interactive Demo</span>
            </div>
            <h1 className="text-4xl md:text-5xl font-bold mb-4">
              Experience NextTrack
            </h1>
            <p className="text-lg text-white/90 max-w-2xl mx-auto">
              Discover how our emotionally-aware AI matches your mood with the perfect soundtrack
            </p>
          </div>
        </div>
      </div>

      {/* Demo Content */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Stepper */}
        <div className="max-w-4xl mx-auto mb-12">
          <Stepper steps={DEMO_STEPS} currentStep={getCurrentStep()} />
        </div>

        {/* Mood Selector */}
        <div className="max-w-5xl mx-auto mb-8">
          <Card className="p-6">
            <div className="mb-6">
              <h2 className="text-xl font-bold mb-2">Choose Your Experience</h2>
              <p className="text-sm text-muted-foreground">
                Describe how you feel, select a mood, or add context for more personalised results
              </p>
            </div>

            {/* Free-text mood input */}
            <div className="mb-6">
              <MoodTextInput onMoodDetected={handleMoodDetected} />
            </div>

            <MoodSelector
              selectedMood={selectedMood}
              onMoodSelect={handleMoodSelect}
            />

            {/* Context + seed tracks (shown once mood selected) */}
            {selectedMood && !showRecommendations && (
              <div className="mt-6 space-y-4 border-t pt-6">
                <ContextSelector context={context} onChange={setContext} />
                <SeedTrackSearch seeds={seedTracks} onSeedsChange={setSeedTracks} />
              </div>
            )}

            {selectedMood && !selectedPlaylist && !showRecommendations && (
              <div className="mt-6 space-y-2">
                {error && (
                  <p className="text-sm text-red-500 text-center">{error}</p>
                )}
                <div className="flex justify-center">
                  <Button
                    size="lg"
                    onClick={handleGetRecommendations}
                    disabled={isLoading}
                    className="min-w-64"
                  >
                    {isLoading ? (
                      <span className="animate-pulse">Analyzing Your Mood...</span>
                    ) : (
                      'Get Recommendations'
                    )}
                  </Button>
                </div>
              </div>
            )}
          </Card>
        </div>

        {/* Preset Playlists */}
        {!showRecommendations && (
          <div className="max-w-5xl mx-auto mb-8">
            <Card className="p-6">
              <PresetPlaylists
                onSelect={handlePlaylistSelect}
              />
            </Card>
          </div>
        )}

        {/* Results - Playlist UI */}
        {showRecommendations && recommendations.length > 0 && currentTrack && (
          <div id="results" className="scroll-mt-8">
            {/* Results Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
              <div>
                <h2 className="text-2xl font-bold mb-2">Your Personalized Playlist</h2>
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                  <span>Based on your <span className="font-semibold text-foreground capitalize">{selectedMood}</span> mood</span>
                  {apiLatencyMs !== null && (
                    <>
                      <span>•</span>
                      <span>Processed in {apiLatencyMs}ms</span>
                    </>
                  )}
                  {confidence !== null && (
                    <>
                      <span>•</span>
                      <div className="flex items-center gap-1.5 text-green-600">
                        <TrendingUp className="w-4 h-4" />
                        <span className="font-semibold">{confidence}% confidence</span>
                      </div>
                    </>
                  )}
                </div>
              </div>
              <Button variant="outline" onClick={handleReset}>
                Try Another Mood
              </Button>
            </div>

            {/* Analysis Card */}
            <Card className="p-6 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20 border-purple-200 dark:border-purple-800 mb-6">
              <h3 className="font-semibold mb-4">How We Analyzed Your Mood</h3>
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Algorithm Used</div>
                  <div className="font-semibold">Hybrid Emotional v2</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">Features Analyzed</div>
                  <div className="font-semibold">Valence, Energy, Tempo, Dance</div>
                </div>
                <div>
                  <div className="text-sm font-medium text-muted-foreground mb-1">
                    {moodAnalysis ? 'Detected Emotion' : 'Tracks Scanned'}
                  </div>
                  <div className="font-semibold capitalize">
                    {moodAnalysis
                      ? `${moodAnalysis.primary_emotion} (${Math.round(moodAnalysis.confidence * 100)}%)`
                      : '50,000,000+'}
                  </div>
                </div>
              </div>
            </Card>

            {/* Playlist Layout */}
            <div className="grid lg:grid-cols-3 gap-6">
              {/* Playlist Sidebar */}
              <div className="lg:col-span-1">
                <Card className="p-4 sticky top-20">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 rounded bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                      <Music className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h3 className="font-semibold">Your Playlist</h3>
                      <p className="text-xs text-muted-foreground">{recommendations.length} tracks</p>
                    </div>
                  </div>

                  <div className="space-y-2 max-h-[600px] overflow-y-auto pr-2">
                    {recommendations.map((track, index) => (
                      <PlaylistItem
                        key={track.id}
                        track={track}
                        index={index}
                        isActive={index === currentTrackIndex}
                        isPlaying={index === currentTrackIndex && isPlaying}
                        onSelect={() => handleTrackSelect(index)}
                      />
                    ))}
                  </div>
                </Card>
              </div>

              {/* Now Playing */}
              <div className="lg:col-span-2">
                <NowPlaying
                  track={currentTrack}
                  isPlaying={isPlaying}
                  onPlayPause={handlePlayPause}
                  onNext={handleNext}
                  onPrevious={handlePrevious}
                />
              </div>
            </div>

            {/* Bottom CTA */}
            <Card className="p-8 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-center mt-8">
              <h3 className="text-2xl font-bold mb-3">Love What You See?</h3>
              <p className="text-white/90 mb-6 max-w-2xl mx-auto">
                Integrate NextTrack's powerful recommendation engine into your application with our simple API
              </p>
              <div className="flex flex-wrap justify-center gap-3">
                <Button size="lg" variant="secondary">
                  Get API Access
                </Button>
                <Button size="lg" variant="outline" className="bg-white/10 border-white/30 text-white hover:bg-white/20">
                  View Documentation
                </Button>
              </div>
            </Card>
          </div>
        )}

        {/* Empty State */}
        {!selectedMood && (
          <div className="max-w-3xl mx-auto text-center py-12">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
              <Sparkles className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Ready to discover your perfect playlist?</h3>
            <p className="text-muted-foreground">
              Describe how you feel above, or select a mood to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
