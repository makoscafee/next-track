import {
  Sun,
  Moon,
  Cloud,
  Dumbbell,
  Briefcase,
  Sofa,
  PartyPopper,
  Car,
  Brain,
  Users,
  CloudRain,
  Snowflake,
  Flame,
} from "lucide-react";
import type { TimeOfDay, Activity, Weather } from "../../types";
import {
  TIME_OF_DAY_OPTIONS,
  ACTIVITY_OPTIONS,
  WEATHER_OPTIONS,
} from "../../types";

interface ContextSelectorProps {
  timeOfDay?: TimeOfDay;
  activity?: Activity;
  weather?: Weather;
  onTimeChange: (time: TimeOfDay | undefined) => void;
  onActivityChange: (activity: Activity | undefined) => void;
  onWeatherChange: (weather: Weather | undefined) => void;
}

const TIME_ICONS: Record<TimeOfDay, React.ReactNode> = {
  morning: <Sun className="w-4 h-4" />,
  afternoon: <Sun className="w-4 h-4" />,
  evening: <Moon className="w-4 h-4" />,
  night: <Moon className="w-4 h-4" />,
};

const ACTIVITY_ICONS: Record<Activity, React.ReactNode> = {
  workout: <Dumbbell className="w-4 h-4" />,
  work: <Briefcase className="w-4 h-4" />,
  relaxation: <Sofa className="w-4 h-4" />,
  party: <PartyPopper className="w-4 h-4" />,
  commute: <Car className="w-4 h-4" />,
  focus: <Brain className="w-4 h-4" />,
  social: <Users className="w-4 h-4" />,
};

const WEATHER_ICONS: Record<Weather, React.ReactNode> = {
  sunny: <Sun className="w-4 h-4" />,
  rainy: <CloudRain className="w-4 h-4" />,
  cloudy: <Cloud className="w-4 h-4" />,
  cold: <Snowflake className="w-4 h-4" />,
  hot: <Flame className="w-4 h-4" />,
};

interface PillGroupProps<T extends string> {
  label: string;
  options: readonly T[];
  selected?: T;
  onChange: (value: T | undefined) => void;
  icons: Record<T, React.ReactNode>;
}

function PillGroup<T extends string>({
  label,
  options,
  selected,
  onChange,
  icons,
}: PillGroupProps<T>) {
  return (
    <div>
      <label className="block text-sm text-[var(--text-muted)] mb-2">
        {label}
      </label>
      <div className="flex flex-wrap gap-2">
        {options.map((option) => (
          <button
            key={option}
            onClick={() => onChange(selected === option ? undefined : option)}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all
              ${
                selected === option
                  ? "bg-[var(--primary)] text-white"
                  : "bg-[var(--surface)] text-[var(--text-muted)] hover:text-white border border-white/10 hover:border-[var(--primary)]/50"
              }
            `}
          >
            {icons[option]}
            <span className="capitalize">{option}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export default function ContextSelector({
  timeOfDay,
  activity,
  weather,
  onTimeChange,
  onActivityChange,
  onWeatherChange,
}: ContextSelectorProps) {
  return (
    <div className="space-y-4">
      <PillGroup
        label="Time of Day"
        options={TIME_OF_DAY_OPTIONS}
        selected={timeOfDay}
        onChange={onTimeChange}
        icons={TIME_ICONS}
      />
      <PillGroup
        label="Activity"
        options={ACTIVITY_OPTIONS}
        selected={activity}
        onChange={onActivityChange}
        icons={ACTIVITY_ICONS}
      />
      <PillGroup
        label="Weather"
        options={WEATHER_OPTIONS}
        selected={weather}
        onChange={onWeatherChange}
        icons={WEATHER_ICONS}
      />
    </div>
  );
}
