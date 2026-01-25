# NextTrack - Project TODO

This file tracks the implementation progress for the NextTrack music recommendation API.

## Completed

### Phase 1: Foundation (Done)
- [x] Set up project directory structure
- [x] Create Python virtual environment
- [x] Install dependencies (requirements.txt)
- [x] Create Flask application skeleton
- [x] Set up PostgreSQL database with Docker
- [x] Set up Redis cache with Docker
- [x] Create database models (User, Track, Interaction)
- [x] Implement Last.fm API integration (replaced Spotify)
- [x] Create dataset loader for Kaggle Spotify dataset
- [x] Build basic API endpoints
- [x] Test all endpoints working

### API Endpoints Implemented
- [x] `GET /health` - Health check
- [x] `GET /api/v1/tracks/search` - Search tracks (dataset + Last.fm)
- [x] `GET /api/v1/tracks/info` - Get track info from Last.fm
- [x] `GET /api/v1/tracks/<id>/features` - Get audio features
- [x] `POST /api/v1/mood/analyze` - Analyze text for mood (VADER + Transformers)
- [x] `POST /api/v1/mood/recommend` - Mood-based recommendations
- [x] `POST /api/v1/recommend/similar` - Find similar tracks
- [x] `POST /api/v1/recommend` - Hybrid recommendations

---

## 🔴 Critical - COMPLETED

### Model Persistence & Versioning
- [x] Implement model save/load (joblib) - `app/ml/model_persistence.py`
- [x] Create model versioning system - `ModelManager` class
- [x] Set up model artifacts directory (`data/models/`)
- [ ] Auto-save models after training

### Train/Test Data Split
- [x] Create train/test/validation split - `app/ml/data_split.py`
- [x] Holdout set for evaluation metrics
- [ ] Cross-validation setup for model tuning

### Evaluation Framework
- [x] Create `scripts/evaluate.py` for offline metrics
- [x] Implement popularity baseline model - `app/ml/baselines.py`
- [x] Implement random baseline model - `app/ml/baselines.py`
- [x] Content-based baseline model - `app/ml/baselines.py`
- [x] Metrics: Precision@K, Recall@K, NDCG@K, MRR, Coverage, Diversity - `app/ml/metrics.py`
- [ ] Automated evaluation on model changes

---

## Completed

### Phase 2: Content-Based Recommender (Done)
- [x] Implement K-NN based similarity model (`app/ml/content_based.py`)
- [x] Train content-based model on full dataset (586K tracks) - `scripts/train_content_model.py`
- [x] Add caching layer for recommendations (`app/ml/cached_recommender.py`)
- [x] Optimize model performance (batch processing, O(1) track ID lookup, ~20ms latency)
- [x] Write unit tests for recommender (22 tests passing)
- [x] Auto-load model on app startup
- [x] Health endpoint shows model status

---

## 🟡 Important - Phase 2-3

### Data Quality & Preprocessing
- [ ] Handle missing audio features (imputation or filter)
- [ ] Outlier detection for audio features
- [ ] Data validation pipeline (check for nulls, ranges)
- [ ] Feature normalization consistency check

### Cold Start Strategy
- [ ] Implement popularity-based fallback for new users
- [ ] Create genre-preference onboarding endpoint
- [ ] Default recommendations for anonymous users
- [ ] Content-based only mode for cold start

### Search & Results Improvements
- [ ] Add pagination (limit/offset) to search endpoints
- [ ] Cache search results in Redis (5 min TTL)
- [ ] Deduplication of recommendations
- [ ] Filter explicit tracks option

### Explainability
- [ ] Add "reason" field to recommendations
- [ ] Track which model component contributed most
- [ ] Feature contribution scores

---

## Completed

### Phase 3: Collaborative Filtering (Done)
- [x] Generate synthetic user interaction data - `scripts/generate_synthetic_users.py`
  - 6 user archetypes with distinct audio feature preferences
  - 1,000 users × ~50 interactions each = 48,995 total interactions
  - Outputs: users JSON, interactions CSV, sparse interaction matrix
- [x] Implement ALS matrix factorization - `app/ml/collaborative.py`
  - Using `implicit` library for efficient ALS
  - 50 latent factors, ~0.2ms inference latency
- [x] Create CF training script - `scripts/train_collaborative_model.py`
  - Validation tests: recommendations, similar users, coverage
  - Model versioning and persistence
- [x] Build user profile service - `app/services/user_service.py`
  - User CRUD, interaction tracking, listening history
  - User stats and top tracks
- [x] Add user API endpoints - `app/api/v1/user.py`
  - Profile management, history, stats, top tracks
- [x] Add cached CF recommender - `app/ml/cached_recommender.py`
  - Redis caching for user recommendations
  - `init_all_recommenders()` loads both models on startup
- [x] Write unit tests (14 tests passing) - `tests/test_collaborative.py`
- [x] Health endpoint shows both models' status

### Phase 4: Sentiment Analysis Enhancement (Done)
- [x] Install transformers library for better emotion detection
- [x] Add transformer-based emotion classifier (j-hartmann/emotion-english-distilroberta-base)
- [x] Improve Valence-Arousal mapping (research-backed values, intensity modulation)
- [x] Add context detection (time of day, activity, weather keywords)
- [x] Context-aware API endpoints (`/mood/analyze`, `/mood/recommend`)
- [x] Unit tests for context detection and VA mapping (21 tests)

---

## Upcoming

### Phase 5: Hybrid Integration
- [x] Build hybrid combiner with configurable weights (app/ml/hybrid.py)
- [ ] Implement A/B testing framework
- [ ] Add explanation generation for recommendations
- [ ] Optimize recommendation latency (<500ms)
- [ ] Add diversity/serendipity controls

### Phase 6: Demo & Documentation
- [ ] Build React/Vue demo frontend
- [ ] Generate Swagger/OpenAPI documentation
- [ ] Write developer integration guide
- [ ] Create evaluation metrics dashboard
- [ ] Conduct user testing
- [ ] Write final project report

---

## Evaluation Metrics

### Offline Metrics to Implement
- [ ] Precision@K (target: > 0.3)
- [ ] Recall@K (target: > 0.2)
- [ ] NDCG@K (target: > 0.4)
- [ ] Coverage - % of catalog recommended (target: > 30%)
- [ ] Diversity - intra-list diversity (target: > 0.5)

### Technical Metrics to Monitor
- [ ] API Response Time (target: < 500ms p95)
- [ ] Model Inference Time (target: < 100ms)

---

## 🟢 Good to Have - Phase 5-6

### Feedback Loop
- [ ] Track recommendation clicks/plays
- [ ] Implicit feedback collection (skip, replay, save)
- [ ] Model retraining pipeline with new feedback

### Configuration Management
- [ ] Environment configs (dev/staging/prod)
- [ ] Feature flags for A/B testing
- [ ] Configurable model weights via API/config

### Production Readiness
- [ ] Health check includes DB/Redis connectivity
- [ ] Graceful shutdown handling
- [ ] Request timeout handling
- [ ] Memory usage monitoring

---

## Technical Debt / Improvements

- [ ] Add proper error handling across all endpoints
- [ ] Implement API rate limiting
- [ ] Add request validation with Marshmallow schemas
- [ ] Set up logging properly (file + console)
- [ ] Add API authentication (JWT)
- [ ] Create Dockerfile for the Flask app
- [ ] Set up CI/CD pipeline
- [ ] Add integration tests
- [ ] Implement Redis caching for recommendations

---

## Notes

### Last.fm API
- API Key configured in `.env`
- No user auth needed for basic features (search, similar, tags)
- Rate limits: 5 requests/second

### Dataset
- Kaggle Spotify Dataset: 586K+ tracks
- Located at: `data/processed/tracks.csv`
- Audio features: danceability, energy, valence, tempo, acousticness, instrumentalness, speechiness, liveness, loudness, key, mode

### Running the App
```bash
docker-compose up -d          # Start PostgreSQL + Redis
source venv/bin/activate      # Activate virtual environment
python run.py                 # Start Flask on port 5001
```

### Priority Order for Next Session
1. Phase 5: Hybrid Integration (A/B testing, explanations, diversity controls)
2. Cold start handling
3. Data quality & preprocessing improvements

---

*Last updated: January 25, 2026*
