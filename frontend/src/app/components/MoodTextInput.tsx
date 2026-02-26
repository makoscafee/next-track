import React, { useState } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Sparkles, Loader2 } from 'lucide-react';
import { analyzeMood, EMOTION_TO_MOOD } from '../../services/api';
import type { MoodAnalysis } from '../../services/types';

interface MoodTextInputProps {
  onMoodDetected: (moodId: string, analysis: MoodAnalysis) => void;
}

const EXAMPLE_PROMPTS = [
  "I'm feeling pumped for the gym 💪",
  "Rainy day, want something cosy and calm ☔",
  "Can't focus, need concentration music 🎯",
  "Feeling romantic tonight ❤️",
  "Need energy for a long drive 🚗",
];

export function MoodTextInput({ onMoodDetected }: MoodTextInputProps) {
  const [text, setText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAnalysis, setLastAnalysis] = useState<MoodAnalysis | null>(null);

  const handleAnalyze = async () => {
    if (!text.trim()) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const analysis = await analyzeMood(text.trim());
      setLastAnalysis(analysis);
      const moodId = EMOTION_TO_MOOD[analysis.primary_emotion] ?? 'neutral';
      onMoodDetected(moodId, analysis);
    } catch {
      setError('Could not analyze mood. Check that the API is running.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleAnalyze();
    }
  };

  return (
    <Card className="p-5 border-purple-200 dark:border-purple-800 bg-gradient-to-br from-purple-50/60 to-pink-50/60 dark:from-purple-950/20 dark:to-pink-950/20">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-semibold text-purple-700 dark:text-purple-300">
          Or describe how you feel
        </span>
      </div>

      <textarea
        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
        rows={2}
        placeholder="e.g. I'm feeling really stressed and need something to calm me down…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
      />

      {/* Example prompts */}
      <div className="flex flex-wrap gap-1.5 mt-2 mb-3">
        {EXAMPLE_PROMPTS.map((prompt) => (
          <button
            key={prompt}
            onClick={() => setText(prompt)}
            className="text-xs px-2 py-1 rounded-full border border-purple-200 dark:border-purple-700 text-purple-700 dark:text-purple-300 hover:bg-purple-100 dark:hover:bg-purple-900/40 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <Button
          onClick={handleAnalyze}
          disabled={!text.trim() || isAnalyzing}
          size="sm"
          className="bg-purple-600 hover:bg-purple-700"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin" />
              Analyzing…
            </>
          ) : (
            <>
              <Sparkles className="w-3.5 h-3.5 mr-1.5" />
              Analyze Mood
            </>
          )}
        </Button>

        {lastAnalysis && !isAnalyzing && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Detected:</span>
            <Badge variant="secondary" className="capitalize">
              {lastAnalysis.primary_emotion}
            </Badge>
            <span className="text-xs">
              {Math.round(lastAnalysis.confidence * 100)}% confidence
            </span>
          </div>
        )}

        {error && (
          <span className="text-xs text-destructive">{error}</span>
        )}
      </div>
    </Card>
  );
}
