import React from 'react';
import { Link } from 'react-router';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { FeaturesSection } from '../components/FeaturesSection';
import { APIDocumentation } from '../components/APIDocumentation';
import { Music2, Sparkles, ArrowRight, Dumbbell, Coffee, Moon, Briefcase } from 'lucide-react';

export function Home() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 text-white overflow-hidden">
        <div className="absolute inset-0 bg-black/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 py-24 text-center">
          <div className="flex justify-center mb-6">
            <div className="bg-white/10 backdrop-blur-sm rounded-full p-6">
              <Music2 className="w-16 h-16" />
            </div>
          </div>
          <h1 className="text-5xl md:text-6xl font-bold mb-6">
            NextTrack
          </h1>
          <p className="text-xl md:text-2xl mb-4 text-white/90 max-w-3xl mx-auto">
            Emotionally-Aware Music Recommendations
          </p>
          <p className="text-lg text-white/80 max-w-2xl mx-auto mb-8">
            The first API that combines hybrid filtering, emotional intelligence, 
            and audio feature analysis for truly personalized music discovery
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" variant="secondary" className="font-semibold">
              Get API Access
            </Button>
            <Button size="lg" variant="outline" className="bg-white/10 border-white/30 text-white hover:bg-white/20">
              View Documentation
            </Button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-8 mt-16 max-w-3xl mx-auto">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">94%</div>
              <div className="text-sm text-white/80">Match Accuracy</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">&lt;150ms</div>
              <div className="text-sm text-white/80">Avg Response Time</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">50M+</div>
              <div className="text-sm text-white/80">Tracks Analyzed</div>
            </div>
          </div>
        </div>
      </div>

      {/* Demo CTA Section */}
      <div className="py-16 bg-background">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <div className="inline-flex items-center gap-2 bg-primary/10 text-primary px-4 py-2 rounded-full mb-4">
              <Sparkles className="w-4 h-4" />
              <span className="text-sm font-semibold">Interactive Demo</span>
            </div>
            <h2 className="text-3xl font-bold mb-4">Experience NextTrack in Action</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto mb-8">
              Select your current mood and see how our AI-powered recommendation engine 
              delivers perfectly matched tracks based on emotional context
            </p>
            <Link to="/demo">
              <Button size="lg" className="group">
                Try Interactive Demo
                <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
            </Link>
          </div>

          {/* Preview Cards */}
          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto mt-12">
            <Card className="p-6 text-center hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">😊</span>
              </div>
              <h3 className="font-semibold mb-2">Select Your Mood</h3>
              <p className="text-sm text-muted-foreground">
                Choose from 8 emotional states to match your current feeling
              </p>
            </Card>
            <Card className="p-6 text-center hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 rounded-full bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center mx-auto mb-4">
                <Sparkles className="w-6 h-6 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="font-semibold mb-2">AI Analysis</h3>
              <p className="text-sm text-muted-foreground">
                Our engine analyzes emotional context and audio features
              </p>
            </Card>
            <Card className="p-6 text-center hover:shadow-lg transition-shadow">
              <div className="w-12 h-12 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto mb-4">
                <Music2 className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="font-semibold mb-2">Perfect Matches</h3>
              <p className="text-sm text-muted-foreground">
                Get personalized recommendations with detailed insights
              </p>
            </Card>
          </div>
        </div>
      </div>

      {/* Comparison Section */}
      <div className="py-16 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Curated for Every Moment</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Pre-made playlists powered by emotional intelligence for any activity or time of day
            </p>
          </div>

          {/* Quick Playlists Preview */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-5xl mx-auto mb-12">
            <Card className="group cursor-pointer overflow-hidden hover:shadow-xl transition-all duration-300 hover:scale-105">
              <div className="h-2 bg-gradient-to-r from-orange-500 to-red-500" />
              <div className="p-4">
                <div className="text-orange-600 mb-3 transform group-hover:scale-110 transition-transform">
                  <Dumbbell className="w-6 h-6" />
                </div>
                <h3 className="font-semibold mb-1 text-sm">Workout Power</h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  High-energy tracks to fuel your gym session
                </p>
              </div>
            </Card>

            <Card className="group cursor-pointer overflow-hidden hover:shadow-xl transition-all duration-300 hover:scale-105">
              <div className="h-2 bg-gradient-to-r from-blue-500 to-cyan-500" />
              <div className="p-4">
                <div className="text-blue-600 mb-3 transform group-hover:scale-110 transition-transform">
                  <Briefcase className="w-6 h-6" />
                </div>
                <h3 className="font-semibold mb-1 text-sm">Deep Focus</h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  Concentration music for productivity
                </p>
              </div>
            </Card>

            <Card className="group cursor-pointer overflow-hidden hover:shadow-xl transition-all duration-300 hover:scale-105">
              <div className="h-2 bg-gradient-to-r from-amber-500 to-yellow-500" />
              <div className="p-4">
                <div className="text-amber-600 mb-3 transform group-hover:scale-110 transition-transform">
                  <Coffee className="w-6 h-6" />
                </div>
                <h3 className="font-semibold mb-1 text-sm">Morning Routine</h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  Start your day with positive vibes
                </p>
              </div>
            </Card>

            <Card className="group cursor-pointer overflow-hidden hover:shadow-xl transition-all duration-300 hover:scale-105">
              <div className="h-2 bg-gradient-to-r from-indigo-500 to-purple-500" />
              <div className="p-4">
                <div className="text-indigo-600 mb-3 transform group-hover:scale-110 transition-transform">
                  <Moon className="w-6 h-6" />
                </div>
                <h3 className="font-semibold mb-1 text-sm">Evening Wind Down</h3>
                <p className="text-xs text-muted-foreground line-clamp-2">
                  Relaxing tunes to end your day
                </p>
              </div>
            </Card>
          </div>

          <div className="text-center">
            <Link to="/demo">
              <Button variant="outline" size="lg">
                Explore All Playlists
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* How We Compare Section */}
      <div className="py-16 bg-background">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">How We Compare</h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              See how NextTrack stands out from traditional music recommendation platforms
            </p>
          </div>

          <Card className="p-6 max-w-5xl mx-auto">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-4 px-4">Feature</th>
                    <th className="text-center py-4 px-4 font-bold text-primary">NextTrack</th>
                    <th className="text-center py-4 px-4">Spotify</th>
                    <th className="text-center py-4 px-4">Pandora</th>
                    <th className="text-center py-4 px-4">Last.fm</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b">
                    <td className="py-4 px-4">Emotional Intelligence</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-4 px-4">Real-time Mood Detection</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-4 px-4">Hybrid Filtering</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">Partial</td>
                    <td className="text-center py-4 px-4">✅</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-4 px-4">Audio Feature Analysis</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">Partial</td>
                    <td className="text-center py-4 px-4">❌</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-4 px-4">Open API Access</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">Limited</td>
                    <td className="text-center py-4 px-4">Limited</td>
                    <td className="text-center py-4 px-4">✅</td>
                  </tr>
                  <tr className="border-b">
                    <td className="py-4 px-4">Context Awareness</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">Partial</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                  </tr>
                  <tr>
                    <td className="py-4 px-4">Sentiment Analysis</td>
                    <td className="text-center py-4 px-4">✅</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                    <td className="text-center py-4 px-4">❌</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      </div>

      {/* Features Section */}
      <FeaturesSection />

      {/* API Documentation */}
      <APIDocumentation />

      {/* CTA Section */}
      <div className="py-16 bg-gradient-to-br from-purple-600 via-pink-600 to-blue-600 text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
          <p className="text-lg text-white/90 mb-8">
            Join thousands of developers using NextTrack to power their music applications
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" variant="secondary" className="font-semibold">
              Sign Up for Free
            </Button>
            <Button size="lg" variant="outline" className="bg-white/10 border-white/30 text-white hover:bg-white/20">
              Contact Sales
            </Button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-muted py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Music2 className="w-6 h-6" />
                <span className="font-bold text-lg">NextTrack</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Emotionally-aware music recommendations for the modern world
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-3">Product</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground">Features</a></li>
                <li><a href="#" className="hover:text-foreground">Pricing</a></li>
                <li><a href="#" className="hover:text-foreground">Documentation</a></li>
                <li><a href="#" className="hover:text-foreground">API Reference</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3">Company</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground">About</a></li>
                <li><a href="#" className="hover:text-foreground">Blog</a></li>
                <li><a href="#" className="hover:text-foreground">Careers</a></li>
                <li><a href="#" className="hover:text-foreground">Contact</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-3">Legal</h4>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-foreground">Privacy</a></li>
                <li><a href="#" className="hover:text-foreground">Terms</a></li>
                <li><a href="#" className="hover:text-foreground">Security</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t pt-8 text-center text-sm text-muted-foreground">
            <p>© 2026 NextTrack. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}