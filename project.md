# NextTrack: Music Recommendation API
## Comprehensive Implementation Plan

**CM3070 Final Project – University of London**

---

## Executive Summary

NextTrack is an emotionally-aware, context-sensitive music recommendation API that differentiates itself from existing solutions (Spotify, Pandora, Last.fm) by combining:

1. **Hybrid Filtering**: Content-based + Collaborative + Sentiment-aware
2. **Emotional Intelligence**: Real-time mood detection from social media/text input
3. **Audio Feature Analysis**: Leveraging Spotify's audio features (valence, energy, tempo, danceability)
4. **Open Access API**: RESTful interface for developers to integrate personalized recommendations

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT LAYER                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  Web App     │  │  Mobile App  │  │  3rd Party   │  │  Demo App    │    │
│  │  (Demo)      │  │  (Optional)  │  │  Developers  │  │  Frontend    │    │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API GATEWAY LAYER                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    Flask REST API (Flask-RESTful)                     │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐        │   │
│  │  │ /recommend │ │ /mood      │ │ /user      │ │ /tracks    │        │   │
│  │  │ /similar   │ │ /analyze   │ │ /history   │ │ /features  │        │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           BUSINESS LOGIC LAYER                               │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐       │
│  │   Recommendation   │  │    Sentiment      │  │   User Profile    │       │
│  │      Engine        │  │    Analyzer       │  │     Manager       │       │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘       │
│           │                      │                      │                    │
│  ┌────────┴────────┐            │                      │                    │
│  │                 │            │                      │                    │
│  ▼                 ▼            ▼                      ▼                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────────┐ ┌─────────────────────────┐       │
│  │Content  │ │Collabor.│ │  NLP/       │ │  Feature Extraction     │       │
│  │Based    │ │Filtering│ │  Sentiment  │ │  (Audio Features)       │       │
│  │Filtering│ │(CF)     │ │  Models     │ │                         │       │
│  └─────────┘ └─────────┘ └─────────────┘ └─────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                      │
│  ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐       │
│  │   PostgreSQL      │  │    Redis Cache    │  │   Spotify API     │       │
│  │   (User Data)     │  │   (Sessions/      │  │   (Audio Features)│       │
│  │                   │  │    Predictions)   │  │                   │       │
│  └───────────────────┘  └───────────────────┘  └───────────────────┘       │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    Pre-processed Music Dataset                         │  │
│  │    (Spotify Features + Last.fm Tags + Emotion Labels)                  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Breakdown

| Component | Technology | Purpose |
|-----------|------------|---------|
| API Layer | Flask + Flask-RESTful | REST endpoints, request handling |
| Auth | Flask-JWT-Extended | API key authentication |
| Recommendation Engine | scikit-learn, TensorFlow | ML models for recommendations |
| Sentiment Analysis | VADER, TextBlob, Transformers | Mood detection from text |
| Database | PostgreSQL | User profiles, listening history |
| Cache | Redis | Session data, prediction cache |
| Task Queue | Celery (optional) | Async model training |
| Documentation | Flasgger (Swagger) | Auto-generated API docs |

---

## 2. Data Pipeline Design

### 2.1 Data Sources

#### Primary Dataset: Spotify Million Playlist Dataset
- **Size**: ~1M playlists, 66M tracks
- **Features**: Track metadata, playlist context
- **Access**: Research API access required

#### Secondary Datasets

| Dataset | Size | Features | Use Case |
|---------|------|----------|----------|
| Spotify Audio Features API | Dynamic | valence, energy, tempo, danceability, etc. | Audio-based similarity |
| Last.fm Dataset | 360K users | Tags, play counts, social data | Collaborative filtering |
| Million Song Dataset | 1M songs | Audio features, metadata | Training content-based models |
| FMA (Free Music Archive) | 106K tracks | Full audio + metadata | Deep learning features |
| MoodyLyrics | 2,000 songs | Emotion-labeled lyrics | Emotion classification training |

### 2.2 Audio Features to Extract

Spotify provides these normalized features (0.0-1.0 scale unless noted):

```python
AUDIO_FEATURES = {
    'acousticness': float,     # 0.0-1.0, acoustic confidence
    'danceability': float,     # 0.0-1.0, rhythm/tempo suitability
    'energy': float,           # 0.0-1.0, intensity/activity
    'instrumentalness': float, # 0.0-1.0, vocal content prediction
    'liveness': float,         # 0.0-1.0, audience presence
    'loudness': float,         # -60 to 0 dB
    'speechiness': float,      # 0.0-1.0, spoken words
    'tempo': float,            # BPM (typical 50-200)
    'valence': float,          # 0.0-1.0, musical positivity
    'mode': int,               # 0 (minor) or 1 (major)
    'key': int,                # 0-11 pitch class notation
    'time_signature': int      # 3-7 beats per measure
}
```

### 2.3 Data Pipeline Workflow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Extract   │───▶│  Transform  │───▶│   Enrich    │───▶│    Load     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                  │                  │
      ▼                  ▼                  ▼                  ▼
 - Spotify API      - Normalize       - Add emotion      - PostgreSQL
 - Last.fm API      - Handle missing    labels           - Feature vectors
 - CSV datasets     - Feature scaling - Add mood tags    - User profiles
                    - One-hot encode  - Sentiment scores
```

### 2.4 Data Collection Script Structure

```python
# data_pipeline/
├── __init__.py
├── collectors/
│   ├── spotify_collector.py    # Spotipy wrapper for audio features
│   ├── lastfm_collector.py     # Last.fm API for tags/social data
│   └── dataset_loader.py       # Load CSV/parquet datasets
├── processors/
│   ├── feature_engineer.py     # Create derived features
│   ├── normalizer.py           # StandardScaler, MinMaxScaler
│   └── emotion_labeler.py      # Label tracks with emotions
├── storage/
│   ├── database.py             # SQLAlchemy models
│   └── cache.py                # Redis caching layer
└── config.py                   # API keys, DB connections
```

---

## 3. Machine Learning Model Design

### 3.1 Hybrid Recommendation Architecture

NextTrack uses a **three-component hybrid system**:

```
                    ┌─────────────────────────────────────┐
                    │         HYBRID COMBINER             │
                    │   (Weighted Score Aggregation)      │
                    └─────────────────────────────────────┘
                           ▲           ▲           ▲
                           │           │           │
              ┌────────────┘           │           └────────────┐
              │                        │                        │
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │   CONTENT-BASED │    │  COLLABORATIVE  │    │   SENTIMENT-    │
    │    FILTERING    │    │    FILTERING    │    │     AWARE       │
    │                 │    │                 │    │                 │
    │ Audio Features  │    │ User-Item Matrix│    │ Mood → Music    │
    │ Cosine Simil.   │    │ Matrix Factor.  │    │ Valence-Energy  │
    │ K-NN            │    │ SVD/NMF/ALS     │    │ Mapping         │
    └─────────────────┘    └─────────────────┘    └─────────────────┘
           (40%)                  (35%)                  (25%)
```

### 3.2 Content-Based Filtering Model

Uses audio features to find similar tracks:

```python
class ContentBasedRecommender:
    """
    Recommends songs based on audio feature similarity.
    Uses cosine similarity on normalized feature vectors.
    """
    
    def __init__(self, n_neighbors=50):
        self.features = [
            'danceability', 'energy', 'valence', 'tempo',
            'acousticness', 'instrumentalness', 'speechiness'
        ]
        self.scaler = StandardScaler()
        self.nn_model = NearestNeighbors(
            n_neighbors=n_neighbors,
            metric='cosine',
            algorithm='brute'  # or 'ball_tree' for large datasets
        )
        
    def fit(self, track_features_df):
        """Fit model on track feature dataframe."""
        X = self.scaler.fit_transform(track_features_df[self.features])
        self.nn_model.fit(X)
        self.track_ids = track_features_df['track_id'].values
        
    def recommend(self, seed_track_features, n_recommendations=10):
        """Get similar tracks to seed."""
        X = self.scaler.transform([seed_track_features])
        distances, indices = self.nn_model.kneighbors(X, n_neighbors=n_recommendations+1)
        
        recommendations = []
        for idx, dist in zip(indices[0][1:], distances[0][1:]):  # Skip seed
            recommendations.append({
                'track_id': self.track_ids[idx],
                'similarity_score': 1 - dist  # Convert distance to similarity
            })
        return recommendations
```

### 3.3 Collaborative Filtering Model

Uses matrix factorization on user-track interactions:

```python
class CollaborativeFilteringRecommender:
    """
    Uses SVD matrix factorization for collaborative filtering.
    Predicts user preferences based on similar users' behavior.
    """
    
    def __init__(self, n_factors=50, regularization=0.1):
        self.n_factors = n_factors
        self.model = None
        
    def fit(self, interaction_matrix):
        """
        Fit on user-item interaction matrix.
        interaction_matrix: scipy.sparse matrix (users x tracks)
        """
        from implicit.als import AlternatingLeastSquares
        
        self.model = AlternatingLeastSquares(
            factors=self.n_factors,
            regularization=0.1,
            iterations=50,
            use_gpu=False
        )
        self.model.fit(interaction_matrix)
        
    def recommend_for_user(self, user_id, user_items, n_recommendations=10):
        """Get recommendations for a specific user."""
        ids, scores = self.model.recommend(
            user_id,
            user_items[user_id],
            N=n_recommendations,
            filter_already_liked_items=True
        )
        return [{'track_id': tid, 'cf_score': score} 
                for tid, score in zip(ids, scores)]
```

### 3.4 Sentiment-Aware Recommendation Model

Maps detected mood to music features using the Valence-Arousal model:

```python
class SentimentAwareRecommender:
    """
    Maps user's detected emotion to appropriate music.
    Uses the Russell's Circumplex Model of Affect.
    
    Valence (positivity) ↔ Music Valence
    Arousal (energy) ↔ Music Energy
    """
    
    # Emotion to (valence, energy) mapping
    EMOTION_MAP = {
        'happy': (0.8, 0.7),
        'excited': (0.7, 0.9),
        'calm': (0.6, 0.3),
        'relaxed': (0.65, 0.25),
        'sad': (0.2, 0.3),
        'angry': (0.3, 0.85),
        'anxious': (0.4, 0.7),
        'melancholic': (0.35, 0.4),
        'energetic': (0.65, 0.85),
        'peaceful': (0.55, 0.2)
    }
    
    def __init__(self, track_features_df):
        self.tracks = track_features_df
        
    def recommend_for_mood(self, detected_emotion, n_recommendations=10):
        """Find tracks matching the emotional state."""
        target_valence, target_energy = self.EMOTION_MAP.get(
            detected_emotion, (0.5, 0.5)
        )
        
        # Calculate euclidean distance in valence-energy space
        self.tracks['mood_distance'] = np.sqrt(
            (self.tracks['valence'] - target_valence)**2 +
            (self.tracks['energy'] - target_energy)**2
        )
        
        # Get closest matches
        recommendations = self.tracks.nsmallest(n_recommendations, 'mood_distance')
        return recommendations[['track_id', 'valence', 'energy', 'mood_distance']].to_dict('records')
```

### 3.5 Hybrid Combiner

```python
class HybridRecommender:
    """
    Combines all three recommendation strategies with configurable weights.
    """
    
    def __init__(self, content_weight=0.4, collab_weight=0.35, sentiment_weight=0.25):
        self.weights = {
            'content': content_weight,
            'collaborative': collab_weight,
            'sentiment': sentiment_weight
        }
        self.content_model = ContentBasedRecommender()
        self.collab_model = CollaborativeFilteringRecommender()
        self.sentiment_model = SentimentAwareRecommender()
        
    def recommend(self, user_id, seed_tracks=None, mood=None, n_recommendations=10):
        """
        Generate hybrid recommendations.
        
        Args:
            user_id: User identifier
            seed_tracks: List of track IDs for content-based
            mood: Detected/specified mood for sentiment-aware
            n_recommendations: Number of tracks to return
        """
        all_scores = defaultdict(float)
        
        # Content-based component
        if seed_tracks:
            content_recs = self.content_model.recommend(seed_tracks)
            for rec in content_recs:
                all_scores[rec['track_id']] += rec['similarity_score'] * self.weights['content']
        
        # Collaborative filtering component
        if user_id:
            cf_recs = self.collab_model.recommend_for_user(user_id)
            for rec in cf_recs:
                all_scores[rec['track_id']] += rec['cf_score'] * self.weights['collaborative']
        
        # Sentiment-aware component
        if mood:
            mood_recs = self.sentiment_model.recommend_for_mood(mood)
            for rec in mood_recs:
                # Convert distance to score (closer = higher)
                score = 1 / (1 + rec['mood_distance'])
                all_scores[rec['track_id']] += score * self.weights['sentiment']
        
        # Sort by combined score
        sorted_tracks = sorted(all_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_tracks[:n_recommendations]
```

---

## 4. Sentiment Analysis Module

### 4.1 Text-Based Mood Detection

```python
class MoodAnalyzer:
    """
    Analyzes text input to detect user's emotional state.
    Supports: direct text input, social media posts (Twitter-style)
    """
    
    def __init__(self):
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
        from transformers import pipeline
        
        self.vader = SentimentIntensityAnalyzer()
        self.emotion_classifier = pipeline(
            "text-classification",
            model="j-hartmann/emotion-english-distilroberta-base",
            return_all_scores=True
        )
        
    def analyze_text(self, text):
        """
        Analyze text and return mood classification.
        
        Returns:
            {
                'primary_emotion': str,
                'confidence': float,
                'valence': float,
                'arousal': float,
                'all_emotions': dict
            }
        """
        # VADER for valence (sentiment polarity)
        vader_scores = self.vader.polarity_scores(text)
        valence = (vader_scores['compound'] + 1) / 2  # Normalize to 0-1
        
        # Transformer model for emotion classification
        emotions = self.emotion_classifier(text)[0]
        emotion_dict = {e['label']: e['score'] for e in emotions}
        primary_emotion = max(emotions, key=lambda x: x['score'])
        
        # Map to arousal
        arousal = self._emotion_to_arousal(primary_emotion['label'])
        
        return {
            'primary_emotion': primary_emotion['label'],
            'confidence': primary_emotion['score'],
            'valence': valence,
            'arousal': arousal,
            'all_emotions': emotion_dict
        }
    
    def _emotion_to_arousal(self, emotion):
        """Map discrete emotion to arousal level."""
        arousal_map = {
            'anger': 0.85, 'fear': 0.75, 'surprise': 0.7,
            'joy': 0.65, 'sadness': 0.3, 'disgust': 0.5,
            'neutral': 0.5
        }
        return arousal_map.get(emotion.lower(), 0.5)
```

### 4.2 Context Detection (Optional Enhancement)

```python
class ContextDetector:
    """
    Detects contextual factors that influence music preference.
    """
    
    def detect_context(self, user_data):
        """
        Analyze various contextual signals.
        
        Inputs can include:
        - Time of day
        - Day of week
        - Recent listening history
        - Activity level (if wearable data available)
        - Weather (via external API)
        """
        context = {}
        
        # Time-based context
        hour = datetime.now().hour
        if 5 <= hour < 9:
            context['time_period'] = 'morning'
            context['suggested_energy'] = 0.5  # Wake-up music
        elif 9 <= hour < 12:
            context['time_period'] = 'late_morning'
            context['suggested_energy'] = 0.7
        elif 12 <= hour < 17:
            context['time_period'] = 'afternoon'
            context['suggested_energy'] = 0.6
        elif 17 <= hour < 21:
            context['time_period'] = 'evening'
            context['suggested_energy'] = 0.65
        else:
            context['time_period'] = 'night'
            context['suggested_energy'] = 0.3  # Relaxing music
            
        return context
```

---

## 5. REST API Design

### 5.1 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recommend` | POST | Get personalized recommendations |
| `/api/v1/recommend/similar` | POST | Find similar tracks |
| `/api/v1/mood/analyze` | POST | Analyze text for mood |
| `/api/v1/mood/recommend` | POST | Get mood-based recommendations |
| `/api/v1/user/profile` | GET/PUT | User preferences |
| `/api/v1/user/history` | GET/POST | Listening history |
| `/api/v1/tracks/{id}/features` | GET | Get track audio features |
| `/api/v1/health` | GET | API health check |

### 5.2 Request/Response Examples

**POST /api/v1/recommend**
```json
// Request
{
    "user_id": "user_123",
    "seed_tracks": ["spotify:track:abc123", "spotify:track:def456"],
    "mood": "energetic",
    "context": {
        "activity": "workout",
        "time_of_day": "morning"
    },
    "limit": 10,
    "preferences": {
        "exclude_explicit": true,
        "min_popularity": 30
    }
}

// Response
{
    "status": "success",
    "recommendations": [
        {
            "track_id": "spotify:track:xyz789",
            "name": "Track Name",
            "artist": "Artist Name",
            "score": 0.89,
            "audio_features": {
                "valence": 0.72,
                "energy": 0.85,
                "danceability": 0.78
            },
            "reason": "Similar to your seed tracks, matches energetic mood"
        }
    ],
    "metadata": {
        "algorithm_version": "1.0.0",
        "processing_time_ms": 145,
        "weights_used": {
            "content": 0.4,
            "collaborative": 0.35,
            "sentiment": 0.25
        }
    }
}
```

**POST /api/v1/mood/analyze**
```json
// Request
{
    "text": "Had an amazing day today! Everything is going perfectly.",
    "source": "user_input"
}

// Response
{
    "status": "success",
    "mood_analysis": {
        "primary_emotion": "joy",
        "confidence": 0.92,
        "valence": 0.85,
        "arousal": 0.65,
        "all_emotions": {
            "joy": 0.92,
            "surprise": 0.04,
            "neutral": 0.02,
            "anger": 0.01,
            "sadness": 0.01
        }
    },
    "suggested_music_features": {
        "target_valence": 0.8,
        "target_energy": 0.7,
        "genres": ["pop", "dance", "feel-good"]
    }
}
```

### 5.3 Flask Application Structure

```
nexttrack/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Configuration settings
│   ├── extensions.py            # Flask extensions (db, cache, etc.)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py        # API Blueprint registration
│   │   │   ├── recommend.py     # Recommendation endpoints
│   │   │   ├── mood.py          # Mood analysis endpoints
│   │   │   ├── user.py          # User management endpoints
│   │   │   └── tracks.py        # Track feature endpoints
│   │   └── schemas/
│   │       ├── __init__.py
│   │       └── serializers.py   # Marshmallow schemas
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py              # User SQLAlchemy model
│   │   ├── track.py             # Track model
│   │   └── interaction.py       # User-Track interactions
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── recommendation.py    # Hybrid recommender logic
│   │   ├── mood_analyzer.py     # Sentiment analysis
│   │   ├── spotify_service.py   # Spotify API wrapper
│   │   └── feature_service.py   # Audio feature extraction
│   │
│   └── ml/
│       ├── __init__.py
│       ├── content_based.py     # Content-based model
│       ├── collaborative.py     # CF model
│       ├── sentiment_aware.py   # Mood-based model
│       └── hybrid.py            # Hybrid combiner
│
├── data/
│   ├── raw/                     # Raw downloaded datasets
│   ├── processed/               # Cleaned, processed data
│   └── models/                  # Trained model artifacts
│
├── tests/
│   ├── __init__.py
│   ├── test_api.py
│   ├── test_recommender.py
│   └── test_mood_analyzer.py
│
├── scripts/
│   ├── download_data.py         # Dataset download scripts
│   ├── train_models.py          # Model training pipeline
│   └── seed_database.py         # Populate initial data
│
├── docs/
│   ├── api_documentation.md
│   └── swagger.yaml
│
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run.py                       # Application entry point
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)
**Goal**: Set up project infrastructure and data pipeline

**Tasks**:
- [ ] Set up Python virtual environment and dependencies
- [ ] Create Flask application skeleton
- [ ] Set up PostgreSQL database with SQLAlchemy
- [ ] Implement Spotify API integration (Spotipy)
- [ ] Build data collection scripts
- [ ] Download and preprocess datasets (start with Kaggle Spotify dataset)
- [ ] Create basic database models (User, Track, Interaction)

**Deliverables**:
- Working Flask app with health endpoint
- Data pipeline that can fetch audio features from Spotify
- Database with sample track data

### Phase 2: Content-Based Recommender (Weeks 4-5)
**Goal**: Build the audio-feature based recommendation engine

**Tasks**:
- [ ] Implement feature engineering pipeline
- [ ] Build K-NN based similarity model
- [ ] Create content-based recommendation endpoint
- [ ] Implement track similarity endpoint
- [ ] Add caching layer for feature vectors
- [ ] Write unit tests for recommender

**Deliverables**:
- `/api/v1/recommend/similar` endpoint working
- Model can find similar tracks based on audio features

### Phase 3: Collaborative Filtering (Weeks 6-7)
**Goal**: Add user-based collaborative filtering

**Tasks**:
- [ ] Generate synthetic user interaction data (or use Last.fm)
- [ ] Implement matrix factorization (SVD/ALS)
- [ ] Build user profile management
- [ ] Create listening history tracking
- [ ] Integrate CF into recommendation pipeline

**Deliverables**:
- User registration and history tracking
- CF recommendations for returning users

### Phase 4: Sentiment Analysis (Weeks 8-9)
**Goal**: Add emotional intelligence to recommendations

**Tasks**:
- [ ] Integrate VADER sentiment analyzer
- [ ] Add transformer-based emotion classifier
- [ ] Build Valence-Arousal mapping model
- [ ] Create mood analysis endpoint
- [ ] Create mood-based recommendation endpoint
- [ ] Map emotions to music features

**Deliverables**:
- `/api/v1/mood/analyze` endpoint
- `/api/v1/mood/recommend` endpoint
- Mood influences recommendation results

### Phase 5: Hybrid Integration (Weeks 10-11)
**Goal**: Combine all models into unified recommendation system

**Tasks**:
- [ ] Build hybrid combiner with configurable weights
- [ ] Implement A/B testing framework for weights
- [ ] Add explanation generation for recommendations
- [ ] Optimize recommendation latency
- [ ] Add diversity/serendipity controls

**Deliverables**:
- Fully integrated hybrid recommender
- Sub-500ms response times

### Phase 6: Demo & Documentation (Weeks 12-14)
**Goal**: Build demo application and comprehensive documentation

**Tasks**:
- [ ] Build React/Vue demo frontend
- [ ] Generate Swagger/OpenAPI documentation
- [ ] Write developer integration guide
- [ ] Create evaluation metrics dashboard
- [ ] Conduct user testing
- [ ] Write final project report

**Deliverables**:
- Interactive demo application
- Complete API documentation
- Project report with evaluation results

---

## 7. Evaluation Metrics

### 7.1 Offline Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Precision@K | Relevant items in top K recommendations | > 0.3 |
| Recall@K | Proportion of relevant items found | > 0.2 |
| NDCG@K | Quality of ranking | > 0.4 |
| Coverage | % of catalog recommended | > 30% |
| Diversity | Intra-list diversity (genre/features) | > 0.5 |

### 7.2 Online Metrics (Demo Testing)

| Metric | Description | Target |
|--------|-------------|--------|
| Click-through Rate | Users clicking recommendations | > 15% |
| Listening Completion | Tracks listened > 30 seconds | > 40% |
| User Satisfaction | Survey-based (1-5 scale) | > 3.8 |
| Session Length | Time spent in demo | > 5 min |

### 7.3 Technical Metrics

| Metric | Target |
|--------|--------|
| API Response Time | < 500ms (p95) |
| Model Inference Time | < 100ms |
| API Uptime | > 99% |
| Memory Usage | < 2GB |

---

## 8. Technology Stack Summary

| Category | Technology | Version |
|----------|------------|---------|
| Language | Python | 3.10+ |
| Web Framework | Flask | 3.0+ |
| REST Extension | Flask-RESTful | 0.3.10 |
| Database | PostgreSQL | 15+ |
| ORM | SQLAlchemy | 2.0+ |
| Caching | Redis | 7+ |
| ML Framework | scikit-learn | 1.3+ |
| Deep Learning | TensorFlow/PyTorch | 2.x |
| NLP | transformers, VADER | 4.x |
| Data Processing | pandas, numpy | 2.x |
| Spotify Integration | spotipy | 2.23+ |
| API Documentation | flasgger | 0.9+ |
| Testing | pytest | 7+ |
| Containerization | Docker | 24+ |

---

## 9. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Spotify API rate limits | High | Medium | Implement caching, use datasets |
| Model training time | Medium | Medium | Use pre-trained models, incremental training |
| Cold start problem | High | High | Content-based fallback for new users |
| Data quality issues | Medium | High | Data validation pipeline, synthetic data |
| Scope creep | Medium | High | Strict phase milestones |
| Performance issues | Medium | Medium | Early load testing, caching |

---

## 10. Getting Started Checklist

```bash
# 1. Create project directory
mkdir nexttrack && cd nexttrack

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 3. Install core dependencies
pip install flask flask-restful flask-sqlalchemy flask-cors
pip install spotipy pandas numpy scikit-learn
pip install vaderSentiment transformers
pip install psycopg2-binary redis
pip install flasgger pytest

# 4. Get Spotify API credentials
# Visit: https://developer.spotify.com/dashboard
# Create app, get Client ID and Client Secret

# 5. Download initial dataset
# Visit: https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks
# Or use: https://www.aicrowd.com/challenges/spotify-million-playlist-dataset-challenge

# 6. Set up PostgreSQL database
# createdb nexttrack

# 7. Create .env file with credentials
echo "SPOTIFY_CLIENT_ID=your_id" >> .env
echo "SPOTIFY_CLIENT_SECRET=your_secret" >> .env
echo "DATABASE_URL=postgresql://user:pass@localhost/nexttrack" >> .env

# 8. Run initial setup
python scripts/seed_database.py
```

---

## Next Steps

1. **Immediate**: Set up development environment following checklist
2. **Week 1**: Implement basic Flask app and Spotify API integration
3. **Week 2**: Build data pipeline and populate initial track dataset
4. **Week 3**: Implement content-based recommender prototype

This plan provides a solid foundation for building NextTrack. The phased approach ensures you have working components at each stage, allowing for iterative refinement and early feedback.

**Key Success Factors**:
- Start with a small, working prototype and iterate
- Use existing Spotify audio features rather than extracting your own
- Focus on the hybrid model as your differentiator
- Build evaluation metrics early to track progress
