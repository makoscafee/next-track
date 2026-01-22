# NextTrack: Music Recommendation API

**CM3070 Final Project – University of London**

An emotionally-aware, context-sensitive music recommendation API that combines content-based filtering, collaborative filtering, and sentiment analysis.

## Features

- **Hybrid Recommendation System**: Combines content-based (audio features), collaborative filtering, and sentiment-aware recommendations
- **Mood Analysis**: Analyze text to detect emotions using VADER + Transformer models (7 emotion categories with 99%+ accuracy)
- **Audio Feature Matching**: Find tracks based on danceability, energy, valence, tempo, etc.
- **Last.fm Integration**: Real-time similar tracks, artist info, and tags
- **600K+ Track Dataset**: Pre-loaded Kaggle Spotify dataset with audio features
- **Evaluation Framework**: Built-in metrics (Precision@K, Recall@K, NDCG@K) with baseline comparisons

## Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-RESTful
- **Database**: PostgreSQL 15, Redis 7
- **ML**: scikit-learn, Transformers (DistilRoBERTa), VADER sentiment analysis
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

Response:
```json
{
    "status": "success",
    "mood_analysis": {
        "primary_emotion": "joy",
        "confidence": 0.9936,
        "valence": 0.924,
        "arousal": 0.65,
        "all_emotions": {
            "joy": 0.9936,
            "surprise": 0.0024,
            "neutral": 0.0008,
            ...
        }
    }
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

## Model Evaluation

Run the evaluation framework to compare models against baselines:

```bash
# Run evaluation with synthetic users
python scripts/evaluate.py --n-users 100 --k 5 10 20

# Results saved to data/evaluation_results.json
```

### Metrics Computed
- **Precision@K**: Relevant items in top K recommendations
- **Recall@K**: Proportion of relevant items found
- **NDCG@K**: Normalized Discounted Cumulative Gain
- **MRR**: Mean Reciprocal Rank
- **Coverage**: Percentage of catalog recommended
- **Diversity**: Intra-list diversity based on audio features

### Baseline Models
- **Popularity Baseline**: Recommends most popular tracks
- **Random Baseline**: Random track selection
- **Content-Based Baseline**: Simple feature matching

### Target Metrics (from project.md)
| Metric | Target |
|--------|--------|
| Precision@10 | > 0.3 |
| Recall@10 | > 0.2 |
| NDCG@10 | > 0.4 |
| Coverage | > 30% |

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
│   └── ml/                  # ML models & evaluation
│       ├── content_based.py     # K-NN content filtering
│       ├── collaborative.py     # Matrix factorization (ALS)
│       ├── sentiment_aware.py   # Valence-Arousal mapping
│       ├── hybrid.py            # Weighted hybrid combiner
│       ├── baselines.py         # Baseline models for comparison
│       ├── metrics.py           # Evaluation metrics
│       ├── data_split.py        # Train/test split utilities
│       └── model_persistence.py # Save/load models
├── data/
│   ├── processed/           # Dataset files (tracks.csv)
│   └── models/              # Trained ML model artifacts
├── tests/                   # Test suite
├── scripts/
│   ├── evaluate.py          # Model evaluation script
│   ├── seed_database.py     # Database seeding
│   └── download_data.py     # Dataset download helper
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

### Running the Evaluation

```bash
# Quick evaluation (50 users)
python scripts/evaluate.py --n-users 50 --k 5 10

# Full evaluation (500 users)
python scripts/evaluate.py --n-users 500 --k 5 10 20 --output data/full_evaluation.json
```

### Docker Commands

```bash
docker-compose up -d      # Start databases
docker-compose down       # Stop databases
docker-compose logs -f    # View logs
docker-compose ps         # Check status
```

### Model Persistence

```python
from app.ml import save_model, load_model, ModelManager

# Save a trained model
save_model(model, 'content_based', version='v1.0')

# Load latest model
model = load_model('content_based')

# Use ModelManager for all models
manager = ModelManager()
manager.save_all({'content_based': model1, 'hybrid': model2})
models = manager.load_all()
```

## Implementation Roadmap

See `TODO.md` for current progress and upcoming tasks.

## License

This project is part of CM3070 Final Project at University of London.
