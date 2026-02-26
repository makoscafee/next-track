import React from 'react';
import { Card, CardContent } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';

const examples = {
  request: {
    method: 'POST',
    endpoint: '/api/v1/recommendations',
    body: {
      mood: 'energetic',
      context: 'workout',
      user_id: 'user_123',
      limit: 10,
    },
  },
  response: {
    recommendations: [
      {
        track_id: 'spotify:track:3n3Ppam7vgaVa1iaRUc9Lp',
        title: 'Mr. Brightside',
        artist: 'The Killers',
        match_score: 94,
        audio_features: {
          valence: 0.45,
          energy: 0.89,
          danceability: 0.35,
          tempo: 148,
        },
        reason: 'High energy track matching your workout mood',
      },
    ],
    metadata: {
      processing_time_ms: 127,
      algorithm: 'hybrid_emotional_v2',
      mood_confidence: 0.92,
    },
  },
};

const curlExample = `curl -X POST https://api.nexttrack.ai/v1/recommendations \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "mood": "energetic",
    "context": "workout",
    "user_id": "user_123",
    "limit": 10
  }'`;

const pythonExample = `import requests

response = requests.post(
    'https://api.nexttrack.ai/v1/recommendations',
    headers={
        'Authorization': 'Bearer YOUR_API_KEY',
        'Content-Type': 'application/json'
    },
    json={
        'mood': 'energetic',
        'context': 'workout',
        'user_id': 'user_123',
        'limit': 10
    }
)

recommendations = response.json()`;

const javascriptExample = `const response = await fetch('https://api.nexttrack.ai/v1/recommendations', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    mood: 'energetic',
    context: 'workout',
    user_id: 'user_123',
    limit: 10
  })
});

const recommendations = await response.json();`;

export function APIDocumentation() {
  return (
    <div className="py-16 bg-background">
      <div className="max-w-7xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold mb-4">Developer-Friendly API</h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Simple RESTful API that integrates seamlessly with your application
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-6">
          {/* Request */}
          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold mb-4">Request</h3>
              <div className="bg-muted rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm">
                  <code>{JSON.stringify(examples.request, null, 2)}</code>
                </pre>
              </div>
            </CardContent>
          </Card>

          {/* Response */}
          <Card>
            <CardContent className="p-6">
              <h3 className="font-semibold mb-4">Response</h3>
              <div className="bg-muted rounded-lg p-4 overflow-x-auto">
                <pre className="text-sm">
                  <code>{JSON.stringify(examples.response, null, 2)}</code>
                </pre>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Code Examples */}
        <Card className="mt-6">
          <CardContent className="p-6">
            <h3 className="font-semibold mb-4">Code Examples</h3>
            <Tabs defaultValue="curl">
              <TabsList>
                <TabsTrigger value="curl">cURL</TabsTrigger>
                <TabsTrigger value="python">Python</TabsTrigger>
                <TabsTrigger value="javascript">JavaScript</TabsTrigger>
              </TabsList>
              <TabsContent value="curl">
                <div className="bg-muted rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm">
                    <code>{curlExample}</code>
                  </pre>
                </div>
              </TabsContent>
              <TabsContent value="python">
                <div className="bg-muted rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm">
                    <code>{pythonExample}</code>
                  </pre>
                </div>
              </TabsContent>
              <TabsContent value="javascript">
                <div className="bg-muted rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm">
                    <code>{javascriptExample}</code>
                  </pre>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
