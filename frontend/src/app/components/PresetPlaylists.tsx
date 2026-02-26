import React from 'react';
import { Card } from './ui/card';
import { 
  Dumbbell, 
  Coffee, 
  Moon, 
  Briefcase,
  Utensils,
  Bike,
  Book,
  HeartPulse
} from 'lucide-react';

interface Playlist {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  gradient: string;
  mood: string; // Maps to existing mood system
}

interface PresetPlaylistsProps {
  onSelect: (playlistId: string, mood: string) => void;
}

const playlists: Playlist[] = [
  {
    id: 'workout',
    name: 'Workout Power',
    description: 'High-energy tracks to fuel your gym session',
    icon: <Dumbbell className="w-6 h-6" />,
    color: 'text-orange-600',
    gradient: 'from-orange-500 to-red-500',
    mood: 'energetic',
  },
  {
    id: 'focus',
    name: 'Deep Focus',
    description: 'Concentration music for productivity',
    icon: <Briefcase className="w-6 h-6" />,
    color: 'text-blue-600',
    gradient: 'from-blue-500 to-cyan-500',
    mood: 'focused',
  },
  {
    id: 'morning',
    name: 'Morning Routine',
    description: 'Start your day with positive vibes',
    icon: <Coffee className="w-6 h-6" />,
    color: 'text-amber-600',
    gradient: 'from-amber-500 to-yellow-500',
    mood: 'happy',
  },
  {
    id: 'evening',
    name: 'Evening Wind Down',
    description: 'Relaxing tunes to end your day',
    icon: <Moon className="w-6 h-6" />,
    color: 'text-indigo-600',
    gradient: 'from-indigo-500 to-purple-500',
    mood: 'calm',
  },
  {
    id: 'dining',
    name: 'Dinner Party',
    description: 'Sophisticated background music',
    icon: <Utensils className="w-6 h-6" />,
    color: 'text-pink-600',
    gradient: 'from-pink-500 to-rose-500',
    mood: 'neutral',
  },
  {
    id: 'commute',
    name: 'Daily Commute',
    description: 'Perfect for your journey',
    icon: <Bike className="w-6 h-6" />,
    color: 'text-green-600',
    gradient: 'from-green-500 to-emerald-500',
    mood: 'neutral',
  },
  {
    id: 'study',
    name: 'Study Session',
    description: 'Ambient sounds for learning',
    icon: <Book className="w-6 h-6" />,
    color: 'text-violet-600',
    gradient: 'from-violet-500 to-purple-500',
    mood: 'focused',
  },
  {
    id: 'romance',
    name: 'Romantic Evening',
    description: 'Love songs for special moments',
    icon: <HeartPulse className="w-6 h-6" />,
    color: 'text-red-600',
    gradient: 'from-red-500 to-pink-500',
    mood: 'romantic',
  },
];

export function PresetPlaylists({ onSelect }: PresetPlaylistsProps) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold mb-2">Or Choose a Curated Playlist</h2>
        <p className="text-muted-foreground">
          Pre-made playlists optimized for specific activities and moments
        </p>
      </div>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {playlists.map((playlist) => (
          <Card
            key={playlist.id}
            className="group cursor-pointer overflow-hidden hover:shadow-xl transition-all duration-300 hover:scale-105"
            onClick={() => onSelect(playlist.id, playlist.mood)}
          >
            <div className={`h-2 bg-gradient-to-r ${playlist.gradient}`} />
            <div className="p-4">
              <div className={`${playlist.color} mb-3 transform group-hover:scale-110 transition-transform`}>
                {playlist.icon}
              </div>
              <h3 className="font-semibold mb-1 text-sm">{playlist.name}</h3>
              <p className="text-xs text-muted-foreground line-clamp-2">
                {playlist.description}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}

export { playlists };
