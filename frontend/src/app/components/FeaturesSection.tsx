import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Brain, Activity, Layers, Code } from 'lucide-react';

const features = [
  {
    icon: <Layers className="w-8 h-8" />,
    title: 'Hybrid Filtering',
    description: 'Combines content-based, collaborative, and sentiment-aware filtering for superior recommendations',
    color: 'text-blue-500',
  },
  {
    icon: <Brain className="w-8 h-8" />,
    title: 'Emotional Intelligence',
    description: 'Real-time mood detection from social media and text input to match your emotional state',
    color: 'text-purple-500',
  },
  {
    icon: <Activity className="w-8 h-8" />,
    title: 'Audio Feature Analysis',
    description: 'Leverages valence, energy, tempo, and danceability metrics for precise matching',
    color: 'text-green-500',
  },
  {
    icon: <Code className="w-8 h-8" />,
    title: 'Open Access API',
    description: 'RESTful interface for developers to integrate personalized recommendations',
    color: 'text-orange-500',
  },
];

export function FeaturesSection() {
  return (
    <div className="py-16 bg-muted/30">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Why Choose NextTrack?</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            NextTrack differentiates itself from Spotify, Pandora, and Last.fm with 
            cutting-edge emotional intelligence and context-aware recommendations
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map((feature, index) => (
            <Card key={index} className="border-2 hover:border-primary transition-colors">
              <CardHeader>
                <div className={`mb-4 ${feature.color}`}>
                  {feature.icon}
                </div>
                <CardTitle className="text-lg">{feature.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <CardDescription>{feature.description}</CardDescription>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
