# NextTrack: Music Recommendation API

**CM3070 Final Project – University of London**

An emotionally-aware, context-sensitive music recommendation API that combines content-based filtering, collaborative filtering, and sentiment analysis.

## Features

- **Hybrid Recommendation System**: Combines content-based (audio features), collaborative filtering, and sentiment-aware recommendations
- **Mood Analysis**: Analyze text to detect emotions and get matching music
- **Audio Feature Matching**: Find tracks based on danceability, energy, valence, tempo, etc.
- **Last.fm Integration**: Real-time similar tracks, artist info, and tags
- **600K+ Track Dataset**: Pre-loaded Kaggle Spotify dataset with audio features

## Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-RESTful
- **Database**: PostgreSQL 15, Redis 7
- **ML**: scikit-learn, VADER sentiment analysis
- **APIs**: Last.fm API
- **Data**: Kaggle Spotify Dataset (600K+ tracks)

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Last.fm API account ([Create here](https://www.last.fm/api/account/create))

### 1. Clone and Setup Environment

```bash
cd nexttrack
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start Databases

```bash
docker-compose up -d
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required settings:
```
LASTFM_API_KEY=your_api_key
LASTFM_API_SECRET=your_api_secret
DATABASE_URL=postgresql://nexttrack:nexttrack_dev@localhost:5432/nexttrack_dev
```

### 4. Download Dataset

Download the Kaggle Spotify dataset:
- [Spotify Dataset 1921-2020](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks)

Place `tracks.csv` in `data/processed/`

### 5. Initialize Database

```bash
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 6. Run the Application

```bash
python run.py
```

The API will be available at `http://localhost:5001`

## API Endpoints

### Health Check
```
GET /health
```

### Track Search
```
GET /api/v1/tracks/search?q=blinding+lights&limit=10&source=both
```
- `source`: `dataset`, `lastfm`, or `both`

### Track Info (Last.fm + Audio Features)
```
GET /api/v1/tracks/info?artist=The%20Weeknd&track=Blinding%20Lights
```

### Track Audio Features
```
GET /api/v1/tracks/<track_id>/features
```

### Mood Analysis
```
POST /api/v1/mood/analyze
Content-Type: application/json

{
    "text": "I'm feeling great today!"
}
```

### Mood-Based Recommendations
```
POST /api/v1/mood/recommend
Content-Type: application/json

{
    "mood": "happy",
    "limit": 10
}
```

Or analyze text first:
```json
{
    "text": "I'm feeling energetic and ready to party!",
    "limit": 10
}
```

### Similar Tracks
```
POST /api/v1/recommend/similar
Content-Type: application/json

{
    "artist": "The Weeknd",
    "track": "Blinding Lights",
    "limit": 10
}
```

### Hybrid Recommendations
```
POST /api/v1/recommend
Content-Type: application/json

{
    "seed_tracks": [
        {"name": "Blinding Lights", "artist": "The Weeknd"}
    ],
    "mood": "energetic",
    "limit": 10
}
```

## Project Structure

```
nexttrack/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── config.py            # Configuration
│   ├── extensions.py        # Flask extensions
│   ├── api/v1/              # API endpoints
│   │   ├── recommend.py     # Recommendation endpoints
│   │   ├── mood.py          # Mood analysis endpoints
│   │   ├── tracks.py        # Track endpoints
│   │   └── user.py          # User endpoints
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── track.py
│   │   └── interaction.py
│   ├── services/            # Business logic
│   │   ├── lastfm_service.py
│   │   ├── dataset_service.py
│   │   ├── recommendation.py
│   │   └── mood_analyzer.py
│   └── ml/                  # ML models
│       ├── content_based.py
│       ├── collaborative.py
│       ├── sentiment_aware.py
│       └── hybrid.py
├── data/
│   ├── processed/           # Dataset files (tracks.csv)
│   └── models/              # Trained ML models
├── tests/                   # Test suite
├── scripts/                 # Utility scripts
├── docker-compose.yml       # PostgreSQL + Redis
├── requirements.txt
├── run.py                   # Entry point
└── TODO.md                  # Project task tracking
```

## Development

### Running Tests

```bash
pytest
```

### Docker Commands

```bash
docker-compose up -d      # Start databases
docker-compose down       # Stop databases
docker-compose logs -f    # View logs
```

## Implementation Roadmap

See `TODO.md` for current progress and upcoming tasks.

## License

This project is part of CM3070 Final Project at University of London.
