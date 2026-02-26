import React from 'react';
import { Sun, Moon, Sunset, Coffee, Dumbbell, Briefcase, Music2, Car, BookOpen, Users, Cloud, CloudRain, Thermometer, Flame } from 'lucide-react';
import type { MoodContext } from '../../services/types';

interface ContextSelectorProps {
  context: MoodContext;
  onChange: (context: MoodContext) => void;
}

type PillOption = { id: string; label: string; icon: React.ReactNode };

const TIME_OPTIONS: PillOption[] = [
  { id: 'morning', label: 'Morning', icon: <Coffee className="w-3.5 h-3.5" /> },
  { id: 'afternoon', label: 'Afternoon', icon: <Sun className="w-3.5 h-3.5" /> },
  { id: 'evening', label: 'Evening', icon: <Sunset className="w-3.5 h-3.5" /> },
  { id: 'night', label: 'Night', icon: <Moon className="w-3.5 h-3.5" /> },
];

const ACTIVITY_OPTIONS: PillOption[] = [
  { id: 'workout', label: 'Workout', icon: <Dumbbell className="w-3.5 h-3.5" /> },
  { id: 'work', label: 'Work', icon: <Briefcase className="w-3.5 h-3.5" /> },
  { id: 'relaxation', label: 'Relax', icon: <BookOpen className="w-3.5 h-3.5" /> },
  { id: 'party', label: 'Party', icon: <Music2 className="w-3.5 h-3.5" /> },
  { id: 'commute', label: 'Commute', icon: <Car className="w-3.5 h-3.5" /> },
  { id: 'social', label: 'Social', icon: <Users className="w-3.5 h-3.5" /> },
];

const WEATHER_OPTIONS: PillOption[] = [
  { id: 'sunny', label: 'Sunny', icon: <Sun className="w-3.5 h-3.5" /> },
  { id: 'cloudy', label: 'Cloudy', icon: <Cloud className="w-3.5 h-3.5" /> },
  { id: 'rainy', label: 'Rainy', icon: <CloudRain className="w-3.5 h-3.5" /> },
  { id: 'cold', label: 'Cold', icon: <Thermometer className="w-3.5 h-3.5" /> },
  { id: 'hot', label: 'Hot', icon: <Flame className="w-3.5 h-3.5" /> },
];

function PillGroup({
  label,
  options,
  selected,
  onSelect,
}: {
  label: string;
  options: PillOption[];
  selected?: string;
  onSelect: (id: string | undefined) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</span>
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => {
          const active = selected === opt.id;
          return (
            <button
              key={opt.id}
              onClick={() => onSelect(active ? undefined : opt.id)}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border transition-all ${
                active
                  ? 'bg-purple-600 border-purple-600 text-white'
                  : 'border-border text-muted-foreground hover:border-purple-400 hover:text-purple-600'
              }`}
            >
              {opt.icon}
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}

export function ContextSelector({ context, onChange }: ContextSelectorProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-semibold">Refine with context</span>
        <span className="text-xs text-muted-foreground">(optional)</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-3">
        <PillGroup
          label="Time of day"
          options={TIME_OPTIONS}
          selected={context.time_of_day}
          onSelect={(v) => onChange({ ...context, time_of_day: v })}
        />
        <PillGroup
          label="Activity"
          options={ACTIVITY_OPTIONS}
          selected={context.activity}
          onSelect={(v) => onChange({ ...context, activity: v })}
        />
        <PillGroup
          label="Weather"
          options={WEATHER_OPTIONS}
          selected={context.weather}
          onSelect={(v) => onChange({ ...context, weather: v })}
        />
      </div>
    </div>
  );
}
