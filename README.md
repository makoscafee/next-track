# NextTrack: Music Recommendation API

An emotionally-aware, context-sensitive music recommendation API that combines content-based filtering, collaborative filtering, and sentiment analysis with A/B testing and explainable recommendations.

## Features

- **Hybrid Recommendation System**: Combines content-based (audio features), collaborative filtering, and sentiment-aware recommendations with configurable weights
- **A/B Testing Framework**: Built-in experiment management for comparing recommendation strategies
- **Explainable Recommendations**: Human-readable explanations for why tracks are recommended
- **Diversity & Serendipity Controls**: Balance between relevance and discovery
- **Mood Analysis**: Analyze text to detect emotions using VADER + Transformer models (7 emotion categories with 99%+ accuracy)
- **Context-Aware**: Adapts recommendations based on time of day, activity, and weather
- **Audio Feature Matching**: Find tracks based on danceability, energy, valence, tempo, etc.
- **Last.fm Integration**: Real-time similar tracks, artist info, and tags
- **600K+ Track Dataset**: Pre-loaded Kaggle Spotify dataset with audio features
- **Evaluation Framework**: Built-in metrics (Precision@K, Recall@K, NDCG@K) with baseline comparisons
- **Interactive API Docs**: Swagger UI with live request/response testing for all 25 endpoints

## Tech Stack

- **Backend**: Python 3.10+, Flask, Flask-RESTful
- **Database**: PostgreSQL 15, Redis 7
- **ML**: scikit-learn, Transformers (DistilRoBERTa), VADER sentiment analysis, implicit (ALS)
- **APIs**: Last.fm API, Deezer API (track previews & cover art)
- **Data**: Kaggle Spotify Dataset (600K+ tracks)
- **Frontend**: React 18, Vite, Tailwind CSS, Radix UI (`frontend/`)
- **API Docs**: Flasgger (Swagger UI 2.0)

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

### 2. Configure Environment

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

### 3. Download Dataset

Download the Kaggle Spotify dataset and place both CSV files in `data/processed/`:
- [Spotify Dataset 1921-2020](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks)

```
data/processed/
├── tracks.csv    # 586K+ tracks with audio features
└── artists.csv   # 1.1M artists with genre data (used for genre recommendations)
```

### 4. Start Databases

```bash
docker-compose up -d
```

This starts PostgreSQL 15 on port 5432 and Redis 7 on port 6379.

### 5. Initialize Database

```bash
python -c "from app import create_app; from app.extensions import db; app = create_app(); app.app_context().push(); db.create_all()"
```

### 6. Run the Application

```bash
python run.py
```

The API will be available at `http://localhost:5000`

| URL | Purpose |
|-----|---------|
| `http://localhost:5000/health` | Health check |
| `http://localhost:5000/api/docs/` | Swagger UI (interactive API docs) |
| `http://localhost:5000/api/v1/apispec.json` | Raw OpenAPI spec |

> **Note:** On macOS, port 5000 is used by AirPlay. Use `PORT=5001 python run.py` to run on port 5001 instead — the Swagger UI will then be at `http://localhost:5001/api/docs/`.

### 7. Run the Frontend (Optional)

```bash
cd frontend
npm install
npm run dev
```

The demo UI will be available at `http://localhost:5173`. It proxies all `/api` requests to the backend (configured in `frontend/vite.config.ts`). Make sure the backend is running first.

## API Documentation (Swagger UI)

With the backend running, open **[http://localhost:5000/api/docs/](http://localhost:5000/api/docs/)** in your browser to access the interactive Swagger UI.

> On macOS (AirPlay conflict) use port 5001: **http://localhost:5001/api/docs/**

The Swagger UI lets you:
- Browse all 25 endpoints grouped by tag
- See full request schemas with field types, enums, and examples
- Send live requests and inspect responses directly in the browser
- Authenticate admin endpoints — click **Authorize**, enter `Bearer <token>` (obtain a token via `POST /api/v1/auth/login` first)

The raw OpenAPI 2.0 spec is also available as JSON at:
```
GET /api/v1/apispec.json
```

### Endpoint Groups

| Tag | Endpoints | Description |
|-----|-----------|-------------|
| **Recommendations** | `POST /recommend`, `POST /recommend/similar`, `POST /onboard` | Hybrid recommendations, similar tracks, new-user onboarding |
| **Mood** | `POST /mood/analyze`, `POST /mood/recommend` | Emotion analysis and mood-driven recommendations |
| **Tracks** | `GET /tracks/search`, `GET /tracks/info`, `GET /tracks/{id}/features`, `GET /tracks/preview`, `GET /tracks/preview/search` | Track search, audio features, Deezer previews |
| **User** | `GET/POST/PUT /user/profile`, `GET/POST /user/history`, `GET /user/stats`, `GET /user/top-tracks` | User profiles and listening history |
| **Experiments** | `GET /experiments`, `GET /experiments/{name}`, `GET /experiments/{name}/variant`, `POST /experiments/{name}/metrics`, `POST /feedback` | A/B testing and feedback |
| **Auth** | `POST /auth/login`, `GET /auth/verify` | Admin JWT authentication |
| **Admin** | `GET /admin/stats`, `GET /admin/feedback`, `GET /admin/experiments/{name}`, `GET /admin/health` | Protected dashboard endpoints |

---

## API Endpoints

### Health Check
```
GET /health
```

### Track Search
```
GET /api/v1/tracks/search?q=blinding+lights&limit=10&offset=0&source=both&exclude_explicit=false
```
- `source`: `dataset`, `lastfm`, or `both`
- `offset`: skip N results for pagination (dataset source only)
- `exclude_explicit`: set `true` to filter out explicit tracks
- Response `metadata` includes `total`, `offset`, `limit`, `has_more` for pagination

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
            "neutral": 0.0008
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

### Hybrid Recommendations (with explanations)
```
POST /api/v1/recommend
Content-Type: application/json

{
    "user_id": "user_123",
    "seed_tracks": [
        {"name": "Blinding Lights", "artist": "The Weeknd"}
    ],
    "mood": "energetic",
    "context": {
        "time_of_day": "morning",
        "activity": "workout"
    },
    "limit": 10,
    "include_explanation": true,
    "diversity_factor": 0.3,
    "serendipity_factor": 0.1,
    "preferred_genres": ["electronic", "pop"],
    "exclude_explicit": false
}
```

Response includes explanations:
```json
{
    "status": "success",
    "recommendations": [
        {
            "name": "Dance Monkey",
            "artist": "Tones and I",
            "score": 0.87,
            "detailed_explanation": {
                "reason": "similar_audio",
                "summary": "Recommended for its similar sound",
                "details": ["Similar audio characteristics to tracks you like"],
                "model_contributions": {"content": 0.55, "sentiment": 0.45},
                "context_factors": ["Great for starting your morning", "High energy for your workout"]
            }
        }
    ],
    "metadata": {
        "explanations_included": true
    }
}
```

### A/B Testing Endpoints

**List Experiments**
```
GET /api/v1/experiments
```

**Get Experiment Details**
```
GET /api/v1/experiments/hybrid_weights
```

**Get User's Variant Assignment**
```
GET /api/v1/experiments/hybrid_weights/variant?user_id=user_123
```

**Record Experiment Metric**
```
POST /api/v1/experiments/hybrid_weights/metrics
Content-Type: application/json

{
    "user_id": "user_123",
    "metric_name": "click_rate",
    "value": 0.75
}
```

**Record User Feedback**
```
POST /api/v1/feedback
Content-Type: application/json

{
    "user_id": "user_123",
    "track_id": "track_456",
    "feedback_type": "click"
}
```

Feedback types: `click`, `play`, `skip`, `save`, `listen_time`

### New User Onboarding (Cold Start)
```
POST /api/v1/onboard
Content-Type: application/json

{
    "user_id": "new_user_42",
    "preferred_genres": ["rock", "electronic", "jazz"],
    "energy_preference": "high",
    "mood_preference": "happy"
}
```

Returns initial recommendations using the cold start strategy (genre → preferences → popularity fallback).

### Admin Authentication

Admin endpoints are protected by JWT. Log in to get a token, then include it in subsequent requests.

**Login**
```
POST /api/v1/auth/login
Content-Type: application/json

{
    "username": "admin",
    "password": "nexttrack_admin_2026"
}
```

Response:
```json
{
    "status": "success",
    "access_token": "<jwt-token>",
    "username": "admin"
}
```

**Verify Token**
```
GET /api/v1/auth/verify
Authorization: Bearer <jwt-token>
```

Default credentials (override via environment variables):
```
ADMIN_USERNAME=admin
ADMIN_PASSWORD=nexttrack_admin_2026
```

### Admin Endpoints

All admin endpoints require `Authorization: Bearer <jwt-token>`.

**System Stats**
```
GET /api/v1/admin/stats
Authorization: Bearer <jwt-token>
```

**System Health**
```
GET /api/v1/admin/health
Authorization: Bearer <jwt-token>
```

**Feedback Log**
```
GET /api/v1/admin/feedback
Authorization: Bearer <jwt-token>
```

**Experiment Detail**
```
GET /api/v1/admin/experiments/<experiment_name>
Authorization: Bearer <jwt-token>
```

---

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
│   │   ├── recommend.py     # Recommendation + onboarding endpoints
│   │   ├── mood.py          # Mood analysis endpoints
│   │   ├── tracks.py        # Track search/features endpoints (paginated, cached)
│   │   ├── user.py          # User profile/history endpoints
│   │   ├── experiments.py   # A/B testing endpoints
│   │   ├── auth.py          # Admin login + JWT verification
│   │   └── admin.py         # Admin stats, feedback, health endpoints
│   ├── models/              # Database models
│   │   ├── user.py
│   │   ├── track.py
│   │   └── interaction.py
│   ├── services/            # Business logic
│   │   ├── lastfm_service.py
│   │   ├── dataset_service.py   # Dataset loading, search (paginated), genre enrichment
│   │   ├── recommendation.py    # Hybrid recommendation orchestration
│   │   └── mood_analyzer.py
│   └── ml/                  # ML models & evaluation
│       ├── content_based.py     # K-NN content filtering
│       ├── collaborative.py     # Matrix factorization (ALS)
│       ├── cold_start.py        # Cold start recommender (genre/preferences/popularity)
│       ├── data_quality.py      # Data validation, outlier detection, preprocessing
│       ├── sentiment_aware.py   # Valence-Arousal mapping
│       ├── hybrid.py            # Weighted hybrid combiner
│       ├── ab_testing.py        # A/B testing framework
│       ├── explainer.py         # Recommendation explanations
│       ├── baselines.py         # Baseline models for comparison
│       ├── metrics.py           # Evaluation metrics
│       ├── data_split.py        # Train/test split utilities
│       └── model_persistence.py # Save/load models
├── frontend/               # Demo UI (React 18 + Vite + Tailwind)
│   ├── src/
│   │   ├── app/
│   │   │   ├── pages/
│   │   │   │   └── Demo.tsx         # Main demo page (mood → context → recommendations)
│   │   │   └── components/
│   │   │       ├── MoodSelector.tsx      # Mood button grid
│   │   │       ├── MoodTextInput.tsx     # Free-text mood analysis
│   │   │       ├── ContextSelector.tsx   # Time / activity / weather pills
│   │   │       ├── SeedTrackSearch.tsx   # Deezer track search + seed selection
│   │   │       ├── NowPlaying.tsx        # Player with real audio preview
│   │   │       ├── PlaylistItem.tsx      # Playlist row with preview indicator
│   │   │       └── TrackCard.tsx         # Track card with audio features
│   │   └── services/
│   │       ├── api.ts     # Fetch-based API client + data mapping
│   │       └── types.ts   # TypeScript types for API responses
│   ├── vite.config.ts     # Vite config with /api proxy to backend
│   └── package.json
├── data/
│   ├── processed/           # Dataset files (tracks.csv, artists.csv)
│   └── models/              # Trained ML model artifacts
├── tests/                   # Test suite (183 tests)
├── scripts/
│   ├── evaluate.py          # Model evaluation script
│   ├── seed_database.py     # Database seeding
│   └── download_data.py     # Dataset download helper
├── docker-compose.yml       # PostgreSQL + Redis
├── requirements.txt
├── run.py                   # Entry point (default port 5000)
└── TODO.md                  # Project task tracking
```

## Development

### Running Tests

```bash
# Run all tests (183 tests)
pytest tests/ -v

# Run specific test files
pytest tests/test_phase5.py -v        # Phase 5 tests (52 tests)
pytest tests/test_recommender.py -v   # Recommender tests
pytest tests/test_mood_analyzer.py -v # Mood analyzer tests
pytest tests/test_cold_start.py -v    # Cold start tests (30 tests)
pytest tests/test_data_quality.py -v  # Data quality tests (23 tests)
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

### Phase 5: Hybrid Integration (Completed)

**A/B Testing Framework** (`app/ml/ab_testing.py`)
- `Variant` class with configurable weight, config, and metric tracking
- `Experiment` class with lifecycle management (draft → running → paused → completed)
- `ABTestManager` for managing multiple concurrent experiments
- Consistent user assignment via MD5 hashing (deterministic variant assignment)
- Metric recording and statistical analysis (mean, std, min, max, count)
- Pre-configured experiments:
  - `hybrid_weights`: Compare different model weight configurations
  - `diversity_level`: Low/medium/high diversity settings
  - `serendipity`: With/without serendipity injection

**Explanation Generator** (`app/ml/explainer.py`)
- `RecommendationExplainer` for human-readable recommendation explanations
- Explanation types: `SIMILAR_AUDIO`, `SIMILAR_USERS`, `MOOD_MATCH`, `POPULARITY`, `CONTEXT`, `SERENDIPITY`
- `FeatureContribution` for tracking how each audio feature contributed
- Explanation methods:
  - `explain_content_based()` - Audio similarity explanations
  - `explain_collaborative()` - User similarity explanations
  - `explain_mood_based()` - Mood matching explanations with context factors
  - `explain_hybrid()` - Combined explanations with model contribution breakdown
- Feature-level descriptions (e.g., "high-energy", "calm and relaxed", "great for dancing")
- Context-aware explanation factors (e.g., "Great for starting your morning", "High energy for your workout")

**Diversity Controls** (MMR-based re-ranking)
- Maximal Marginal Relevance algorithm for balancing relevance vs diversity
- `diversity_factor` parameter (0-1): Higher values prioritize diversity over relevance
- Feature similarity calculation for identifying redundant recommendations
- Prevents echo chamber effect by diversifying audio characteristics

**Serendipity Injection**
- `serendipity_factor` parameter (0-1): Fraction of recommendations to replace with discoveries
- Injects lower-scoring but potentially interesting tracks
- Helps users discover new music outside their usual preferences

**Enhanced Hybrid Recommender** (`app/ml/hybrid.py`)
- A/B test integration for dynamic weight configuration
- Explanation generation on demand (`include_explanation` parameter)
- Diversity and serendipity controls with A/B test overrides
- Latency tracking for performance monitoring
- User feedback recording for experiment metrics
- Track feature caching for efficient explanation generation

**A/B Testing API Endpoints** (`app/api/v1/experiments.py`)
- `GET /api/v1/experiments` - List all experiments
- `GET /api/v1/experiments/<name>` - Get experiment details and results
- `GET /api/v1/experiments/<name>/variant` - Get user's variant assignment
- `POST /api/v1/experiments/<name>/metrics` - Record experiment metric
- `POST /api/v1/feedback` - Record user feedback (click, play, skip, save, listen_time)

**Updated Recommendation Endpoint** (`app/api/v1/recommend.py`)
- New parameters:
  - `user_id` - For A/B test assignment and personalization
  - `include_explanation` - Request detailed explanations
  - `diversity_factor` - Override A/B test diversity setting
  - `serendipity_factor` - Override A/B test serendipity setting
  - `context` - Time of day, activity, weather for context-aware recommendations
- Response includes `detailed_explanation` when requested

**Unit Tests** (`tests/test_phase5.py`)
- 52 tests covering:
  - Variant creation, metrics, and statistics
  - Experiment lifecycle and user assignment
  - ABTestManager operations
  - Default experiment creation
  - Explainer initialization and feature categorization
  - Content-based, collaborative, mood-based, and hybrid explanations
  - Explanation formatting
  - Hybrid recommender A/B integration
  - Feature similarity calculation
  - API endpoint tests for experiments, variants, metrics, feedback
  - Recommendation endpoint with diversity/serendipity/explanation parameters

---

### Frontend Demo UI (Completed)

**React 18 + Vite + Tailwind CSS** (`frontend/`)

A polished interactive demo that exposes the full NextTrack API through a clean UI. All API calls go through a Vite dev-server proxy (`/api` → `http://localhost:5001`).

**Features**
- **Free-text mood input** (`MoodTextInput.tsx`) — type how you feel; calls `POST /api/v1/mood/analyze`, auto-selects the detected mood button and shows detected emotion + confidence badge
- **Mood selector** (`MoodSelector.tsx`) — grid of mood buttons (happy, sad, energetic, calm, focused, romantic, neutral)
- **Context pills** (`ContextSelector.tsx`) — three pill groups (Time of day, Activity, Weather) sent as context to the recommendations endpoint
- **Seed track search** (`SeedTrackSearch.tsx`) — debounced Deezer search, up to 3 seed tracks selectable; seeds sent to `POST /api/v1/recommend` for personalized results
- **Real recommendations** (`Demo.tsx`) — calls `POST /api/v1/recommend` (with seeds/context) or `POST /api/v1/mood/recommend` (simple), then enriches results with Deezer cover art and 30-second preview URLs
- **Audio playback** (`NowPlaying.tsx`) — plays Deezer 30-second previews; real-time progress bar with click-to-seek; auto-advances to next track on end; graceful "No preview available" fallback
- **Playlist sidebar** (`PlaylistItem.tsx`) — preview indicator icon (music note) for tracks that have a preview URL

**API Service** (`frontend/src/services/api.ts`)
- `analyzeMood(text)` — maps detected emotion to mood button id via `EMOTION_TO_MOOD`
- `getMoodRecommendations(mood, limit, context)` — simple mood path
- `getRecommendations(request)` — full hybrid path (seeds + context)
- `searchTracksWithPreview(query, limit)` — Deezer track search for seed selection
- `getTrackPreview(artist, track)` — fetch Deezer preview for a single track
- `enrichWithPreviews(apiTracks)` — parallel Deezer preview fetch for all recommendations; gracefully degrades if Deezer lookup fails
- `mapApiTrack(apiTrack, deezer?)` — maps API response fields to the frontend `Track` type (0–1 → 0–100 scaling, `name` → `title`, etc.)

**Running the Frontend**
```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## License

MIT
