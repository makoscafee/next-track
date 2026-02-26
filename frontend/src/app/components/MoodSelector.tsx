import React from 'react';
import { Button } from './ui/button';
import { 
  Smile, 
  Frown, 
  Meh, 
  Heart, 
  Zap, 
  CloudRain,
  Sun,
  Coffee,
  Music
} from 'lucide-react';

interface Mood {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
}

interface MoodSelectorProps {
  selectedMood: string | null;
  onMoodSelect: (moodId: string) => void;
}

const moods: Mood[] = [
  { id: 'happy', label: 'Happy', icon: <Smile className="w-6 h-6" />, color: 'bg-yellow-500' },
  { id: 'energetic', label: 'Energetic', icon: <Zap className="w-6 h-6" />, color: 'bg-orange-500' },
  { id: 'romantic', label: 'Romantic', icon: <Heart className="w-6 h-6" />, color: 'bg-pink-500' },
  { id: 'calm', label: 'Calm', icon: <Sun className="w-6 h-6" />, color: 'bg-blue-400' },
  { id: 'sad', label: 'Sad', icon: <CloudRain className="w-6 h-6" />, color: 'bg-gray-500' },
  { id: 'focused', label: 'Focused', icon: <Coffee className="w-6 h-6" />, color: 'bg-amber-700' },
  { id: 'neutral', label: 'Neutral', icon: <Meh className="w-6 h-6" />, color: 'bg-slate-500' },
  { id: 'party', label: 'Party', icon: <Music className="w-6 h-6" />, color: 'bg-purple-500' },
];

export function MoodSelector({ selectedMood, onMoodSelect }: MoodSelectorProps) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">How are you feeling?</h2>
        <p className="text-muted-foreground">
          Select your current mood to get personalized recommendations
        </p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {moods.map((mood) => (
          <Button
            key={mood.id}
            variant={selectedMood === mood.id ? 'default' : 'outline'}
            className={`h-auto py-6 flex flex-col gap-2 transition-all ${
              selectedMood === mood.id ? mood.color : ''
            }`}
            onClick={() => onMoodSelect(mood.id)}
          >
            {mood.icon}
            <span>{mood.label}</span>
          </Button>
        ))}
      </div>
    </div>
  );
}
