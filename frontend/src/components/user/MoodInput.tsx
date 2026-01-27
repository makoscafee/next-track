import { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import Button from '../common/Button';

interface MoodInputProps {
  onAnalyze: (text: string) => void;
  isLoading?: boolean;
}

const EXAMPLE_PROMPTS = [
  "I'm feeling happy and energetic today!",
  "Feeling a bit melancholic, need some comfort music",
  "Ready for a workout, pump me up!",
  "Relaxing on a rainy evening",
  "It's Friday night, time to party!",
  "Need to focus on work, help me concentrate",
];

export default function MoodInput({ onAnalyze, isLoading = false }: MoodInputProps) {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onAnalyze(text.trim());
    }
  };

  const handleExampleClick = (example: string) => {
    setText(example);
    onAnalyze(example);
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="How are you feeling today? Tell me about your mood..."
            className="w-full h-32 px-5 py-4 bg-[var(--surface)] border border-white/10 rounded-2xl text-white placeholder-[var(--text-muted)] resize-none focus:outline-none focus:border-[var(--primary)] focus:ring-2 focus:ring-[var(--primary)]/20 transition-all"
            disabled={isLoading}
          />
          <Button
            type="submit"
            size="md"
            isLoading={isLoading}
            disabled={!text.trim()}
            className="absolute bottom-4 right-4"
            rightIcon={<Send className="w-4 h-4" />}
          >
            Analyze
          </Button>
        </div>
      </form>

      <div className="mt-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-4 h-4 text-[var(--primary)]" />
          <span className="text-sm text-[var(--text-muted)]">Try an example:</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_PROMPTS.map((prompt, index) => (
            <button
              key={index}
              onClick={() => handleExampleClick(prompt)}
              disabled={isLoading}
              className="px-3 py-1.5 text-sm bg-[var(--surface)] border border-white/10 rounded-full text-[var(--text-muted)] hover:text-white hover:border-[var(--primary)]/50 transition-all disabled:opacity-50"
            >
              {prompt.length > 35 ? prompt.substring(0, 35) + '...' : prompt}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
