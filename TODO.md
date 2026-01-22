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
- [x] `POST /api/v1/mood/analyze` - Analyze text for mood (VADER)
- [x] `POST /api/v1/mood/recommend` - Mood-based recommendations
- [x] `POST /api/v1/recommend/similar` - Find similar tracks
- [x] `POST /api/v1/recommend` - Hybrid recommendations

---

## In Progress

### Phase 2: Content-Based Recommender
- [x] Implement K-NN based similarity model (app/ml/content_based.py)
- [ ] Train content-based model on full dataset
- [ ] Add caching layer for feature vectors
- [ ] Optimize model performance
- [ ] Write unit tests for recommender

---

## Upcoming

### Phase 3: Collaborative Filtering
- [ ] Generate synthetic user interaction data
- [ ] Implement matrix factorization (SVD/ALS)
- [ ] Build user profile management
- [ ] Create listening history tracking
- [ ] Integrate CF into recommendation pipeline

### Phase 4: Sentiment Analysis Enhancement
- [x] Install transformers library for better emotion detection
- [x] Add transformer-based emotion classifier (j-hartmann/emotion-english-distilroberta-base)
- [ ] Improve Valence-Arousal mapping
- [ ] Add context detection (time of day, etc.)

### Phase 5: Hybrid Integration
- [ ] Build hybrid combiner with configurable weights
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

## Technical Debt / Improvements

- [ ] Add proper error handling across all endpoints
- [ ] Implement API rate limiting
- [ ] Add request validation with Marshmallow schemas
- [ ] Set up logging properly (file + console)
- [ ] Add API authentication (JWT)
- [ ] Create Dockerfile for the Flask app
- [ ] Set up CI/CD pipeline
- [ ] Add integration tests

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

---

*Last updated: January 2026*
