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

---

## Development History

### Phase 1: Foundation (Completed)

**Project Setup**
- Created Flask application factory pattern with blueprints
- Set up PostgreSQL 15 + Redis 7 via Docker Compose
- Configured Flask extensions: SQLAlchemy, Migrate, JWT, Flask-Caching, CORS

**Database Models**
- `User`: User accounts with preferences and listening history
- `Track`: Track metadata and audio features
- `Interaction`: User-track interactions (plays, likes, skips)

**Data Integration**
- Integrated Kaggle Spotify Dataset (586,672 tracks with audio features)
- Implemented `DatasetService` for CSV loading and querying
- Added Last.fm API integration for real-time track info and similar tracks

**API Endpoints**
- `GET /health` - Health check with service status
- `GET /api/v1/tracks/search` - Search tracks across dataset + Last.fm
- `GET /api/v1/tracks/info` - Get track info from Last.fm
- `GET /api/v1/tracks/<id>/features` - Get audio features from dataset
- `POST /api/v1/mood/analyze` - Analyze text for mood/emotion
- `POST /api/v1/mood/recommend` - Mood-based recommendations
- `POST /api/v1/recommend/similar` - Find similar tracks
- `POST /api/v1/recommend` - Hybrid recommendations

**Mood Analysis**
- Integrated VADER sentiment analyzer for basic polarity detection
- Added transformer-based emotion classifier (`j-hartmann/emotion-english-distilroberta-base`)
- Implemented Valence-Arousal mapping from 7 emotion categories

---

### Phase 2: Content-Based Recommender (Completed)

**K-NN Similarity Model** (`app/ml/content_based.py`)
- Implemented `ContentBasedRecommender` using scikit-learn's `NearestNeighbors`
- Uses cosine similarity on 7 audio features: danceability, energy, valence, tempo, acousticness, instrumentalness, speechiness
- `StandardScaler` normalization for consistent feature scaling
- Configurable K-NN algorithm (`auto`, `ball_tree`, `kd_tree`, `brute`)

**Training Pipeline** (`scripts/train_content_model.py`)
- Loads and preprocesses 586,672 tracks from dataset
- Handles missing values with median imputation
- Normalizes tempo to 0-1 scale (clips to 0-250 BPM range)
- Filters tracks with >2 missing audio features
- Automated validation tests (4 tests: recommend, recommend_from_track_id, score validation, latency)
- Saves trained model with versioning to `data/models/`

**Performance Optimizations**
- Added O(1) track ID lookup with `_track_id_to_idx` dictionary (replaced O(n) `np.where`)
- Implemented batch recommendation methods:
  - `recommend_batch()` - Get recommendations for multiple feature sets in one call
  - `recommend_from_track_ids_batch()` - Get recommendations for multiple track IDs in one call
- Added `get_track_features()` to retrieve stored features for any track
- Average inference latency: ~20ms (target was <100ms)

**Caching Layer** (`app/ml/cached_recommender.py`)
- `CachedContentRecommender` wrapper with Redis caching support
- Caches recommendation results by feature hash (MD5, 5-minute TTL)
- Caches recommendations by track ID (5-minute TTL)
- Singleton pattern with `get_cached_recommender()` for app-wide access
- `init_cached_recommender()` for automatic model loading on app startup

**App Integration**
- Model auto-loads when Flask app starts via `create_app()`
- Health endpoint (`/health`) now returns model status:
  ```json
  {
    "status": "healthy",
    "service": "nexttrack",
    "models": {
      "content_based": {
        "loaded": true,
        "n_tracks": 586672,
        "n_neighbors": 50,
        "version": "20260125_140025",
        "trained_at": "2026-01-25T14:00:25.825420"
      }
    }
  }
  ```

**Unit Tests** (`tests/test_recommender.py`)
- 22 tests for `ContentBasedRecommender`:
  - Initialization (default and custom algorithm)
  - Model fitting and track ID indexing
  - Single recommendations (dict and array input)
  - Batch recommendations (features and track IDs)
  - Invalid track ID handling
  - Feature retrieval
  - Similarity score validation (range 0-1, sorted descending)
  - Unfitted model edge cases

**Model Persistence** (`app/ml/model_persistence.py`)
- `save_model()` - Save with automatic versioning (timestamp) + metadata JSON
- `load_model()` - Load by version or "latest"
- `ModelManager` class for managing multiple models
- Model artifacts stored in `data/models/` with format: `{model_name}_{version}.joblib`

---

### Phase 3: Collaborative Filtering (Completed)

**Synthetic User Data Generation** (`scripts/generate_synthetic_users.py`)
- Generates realistic user-track interaction patterns
- 6 user archetypes with distinct preferences: `party_lover`, `chill_listener`, `workout_enthusiast`, `melancholic`, `eclectic`, `focus_worker`
- Each archetype has characteristic audio feature preferences (e.g., party lovers prefer high danceability/energy)
- User-track affinity calculation based on feature matching + popularity bias
- Generates interaction types: `play`, `like`, `save` with realistic distributions
- Outputs: `synthetic_users.json`, `synthetic_interactions.csv`, `interaction_matrix.npz`
- Default: 1,000 users × 50 interactions each = ~50K interactions

**ALS Matrix Factorization Model** (`app/ml/collaborative.py`)
- `CollaborativeFilteringRecommender` using `implicit` library's ALS implementation
- Configurable hyperparameters: `n_factors` (latent dimensions), `regularization`, `iterations`
- User and track ID mappings with O(1) lookup via dictionaries
- `recommend_for_user()` - Get personalized recommendations for a user
- `get_similar_users()` - Find users with similar taste profiles
- `filter_already_liked` option to exclude previously interacted tracks

**CF Training Pipeline** (`scripts/train_collaborative_model.py`)
- Loads synthetic interaction data (sparse matrix + ID mappings)
- Trains ALS model with configurable hyperparameters
- Validation tests: user recommendations, similar users, score validation, latency, coverage
- Training time: ~4 seconds for 1K users × 50K tracks
- Average inference latency: ~0.2ms per recommendation request

**User Profile Service** (`app/services/user_service.py`)
- `UserService` class for managing user profiles and interactions
- `get_or_create_user()` - Create new users or retrieve existing
- `record_interaction()` - Track user-track interactions (play, like, save, skip)
- `get_user_history()` - Retrieve listening history with filters
- `get_user_top_tracks()` - Get most played/liked tracks with engagement scoring
- `get_user_stats()` - Listening statistics (total plays, unique tracks, avg rating)
- `get_similar_users_by_taste()` - Find similar users via Jaccard similarity on liked tracks

**User API Endpoints** (`app/api/v1/user.py`)
- `GET /api/v1/user/profile?user_id=X` - Get user profile
- `POST /api/v1/user/profile` - Create user with optional preferences
- `PUT /api/v1/user/profile` - Update user preferences
- `GET /api/v1/user/history?user_id=X` - Get listening history
- `POST /api/v1/user/history` - Record new interaction
- `GET /api/v1/user/stats?user_id=X` - Get user statistics
- `GET /api/v1/user/top-tracks?user_id=X` - Get top tracks

**Cached CF Recommender** (`app/ml/cached_recommender.py`)
- `CachedCollaborativeRecommender` wrapper with Redis caching
- Caches recommendations by user ID (5-minute TTL)
- Caches similar users queries (5-minute TTL)
- `get_cached_cf_recommender()` singleton accessor
- `init_all_recommenders()` loads both content-based and CF models on startup

**App Integration**
- Both models auto-load when Flask app starts
- Health endpoint shows both model statuses:
  ```json
  {
    "status": "healthy",
    "service": "nexttrack",
    "models": {
      "content_based": {
        "loaded": true,
        "n_tracks": 586672,
        "n_neighbors": 50,
        "version": "20260125_140025"
      },
      "collaborative": {
        "loaded": true,
        "n_users": 1000,
        "n_tracks": 50000,
        "n_factors": 50,
        "version": "20260125_140945"
      }
    }
  }
  ```

**Unit Tests** (`tests/test_collaborative.py`)
- 14 tests for `CollaborativeFilteringRecommender`:
  - Initialization with custom hyperparameters
  - Model fitting with sparse interaction matrix
  - User recommendations with score validation
  - Similar users discovery
  - Invalid user handling
  - Already-liked item filtering
  - Different users get different recommendations
  - Integration tests with loaded model

---

### Phase 4: Sentiment Analysis Enhancement (Completed)

**Improved Valence-Arousal Mapping** (`app/services/mood_analyzer.py`, `app/ml/sentiment_aware.py`)
- Research-backed values based on Russell's Circumplex Model of Affect
- Extended emotion vocabulary from 15 to 30+ emotions covering all four quadrants:
  - Q1 (High valence, High arousal): joy, happy, excited, elated, enthusiastic
  - Q2 (Low valence, High arousal): angry, anxious, fear, stressed, frustrated, tense
  - Q3 (Low valence, Low arousal): sad, melancholic, depressed, lonely, bored
  - Q4 (High valence, Low arousal): calm, relaxed, peaceful, serene, content
- Intensity modulation: Confidence scores affect valence/arousal extremity
  - High confidence → values closer to emotion extremes
  - Low confidence → values closer to neutral (0.5, 0.45)
- Transformer emotion mapping for `j-hartmann/emotion-english-distilroberta-base` model output

**Context Detection System**
- Automatic detection from text input:
  - **Time of day**: morning, afternoon, evening, night (from keywords like "breakfast", "midnight", or from timestamp)
  - **Activity**: workout, work, relaxation, party, commute, focus, social
  - **Weather**: sunny, rainy, cloudy, cold, hot
- Regex-based pattern matching for natural language detection
- Fallback to timestamp-based time detection when keywords not present

**Context-Aware Recommendations**
- Context modifiers adjust target valence/arousal:
  - Workout: +8% valence, +20% energy
  - Relaxation: +5% valence, -20% energy
  - Party: +10% valence, +25% energy
  - Night: -2% valence, -15% energy
  - Sunny weather: +8% valence, +5% energy
- Multiple contexts stack additively (e.g., morning workout = extra high energy)
- Values clamped to 0-1 range to prevent overflow

**Updated API Endpoints**
- `POST /api/v1/mood/analyze` now returns context detection:
  ```json
  {
    "status": "success",
    "mood_analysis": {
      "primary_emotion": "joy",
      "confidence": 0.92,
      "valence": 0.85,
      "arousal": 0.72,
      "context": {
        "time_of_day": "morning",
        "activity": "workout",
        "weather": "sunny",
        "detected_from_text": {"time": true, "activity": true, "weather": true}
      },
      "context_adjustment": {
        "valence_delta": 0.21,
        "arousal_delta": 0.35
      }
    }
  }
  ```
- `POST /api/v1/mood/recommend` accepts explicit context override:
  ```json
  {
    "mood": "happy",
    "limit": 10,
    "context": {
      "activity": "workout",
      "time_of_day": "morning"
    }
  }
  ```

**Unit Tests** (`tests/test_mood_analyzer.py`)
- 21 tests covering:
  - Emotion VA map structure and quadrant positioning
  - Target features with and without context
  - Context detection from text and timestamps
  - Activity, weather, and time-of-day detection
  - Context modifier stacking and clamping
  - Intensity modulation for high/low confidence emotions

---

## License

This project is part of CM3070 Final Project at University of London.
