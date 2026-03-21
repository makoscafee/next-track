# NextTrack: An Emotionally-Aware Music Recommendation System
## Final Project Report — CM3070 Final Project
**University of London | March 2026**

**Code Repository:** https://github.com/[username]/nexttrack *(publicly viewable)*

---

# Chapter 1: Introduction (Word count: 912)

## 1.1 Project Overview

Music has long served as a powerful medium for emotional expression and regulation. Yet despite the ubiquity of streaming platforms, the dominant approaches to music recommendation — click-through history, playlist co-occurrence, and demographic profiling — remain largely indifferent to a listener's immediate emotional state. A user who feels anxious before an important morning meeting receives the same algorithmic output as one who is unwinding on a Sunday afternoon, even though their emotional and functional needs are entirely different.

NextTrack addresses this gap. It is a full-stack music recommendation system that fuses three complementary machine learning approaches — audio feature similarity, collaborative filtering, and real-time mood analysis — into a single, configurable hybrid pipeline. The system accepts a natural-language description of the user's emotional state, analyses it using a dual-model NLP pipeline, and returns a ranked list of tracks with human-readable explanations of why each was recommended. The result is a recommendation experience that is simultaneously contextually appropriate and transparent.

## 1.2 Motivation

Three converging problems motivated this project.

**Emotional blindness in current systems.** Commercial platforms such as Spotify, Apple Music, and YouTube Music optimise for engagement metrics — listen-through rate, session length, downstream plays — rather than emotional resonance. Research in affective computing has demonstrated that listeners frequently seek music to regulate mood (Thayer et al., 1994; North & Hargreaves, 1997), yet emotional intent is almost never an explicit input to recommendation algorithms. The gap between what users want — music that matches or constructively shifts their emotional state — and what they receive — music similar to what they played last week — represents a genuine and unmet need.

**Lack of transparency.** The black-box nature of collaborative filtering and deep-learning recommendation models has been identified as a significant barrier to user trust (Tintarev & Masthoff, 2007). Users who understand why a track was recommended are more likely to explore suggestions and provide meaningful feedback, creating a virtuous improvement cycle. Current platforms offer no explanation interface.

**Closed API ecosystem.** The major platforms restrict recommendation functionality behind proprietary APIs with stringent rate limits and terms of service that prohibit research use. This limits the ability of the academic and developer community to experiment with novel recommendation strategies. NextTrack was designed as an open, well-documented REST API with no paywalled functionality.

## 1.3 Project Concept

NextTrack accepts two primary inputs: a natural-language description of the user's current emotional state and context (for example, "I'm anxious but determined, getting ready for a morning workout"), and an optional seed track. The system then:

1. Analyses the emotional content using a dual-model NLP pipeline (VADER sentiment analysis blended with a fine-tuned DistilRoBERTa transformer classifier).
2. Maps the detected emotion to a target region in the Valence × Energy audio feature space using a research-grounded lookup table, then adjusts for contextual signals extracted from the text (time of day, activity, weather).
3. Queries a content-based K-Nearest Neighbour model trained on 586,672 audio tracks, an ALS collaborative filtering model trained on synthetic user interaction data, and a sentiment-aware audio-range filter.
4. Fuses the three ranked candidate lists using configurable weights (default: content 40%, collaborative 35%, sentiment 25%), applies Maximal Marginal Relevance re-ranking for diversity, and deduplicates and interleaves results across sources.
5. Returns an ordered list of recommendations with structured, human-readable explanations for each track, together with audio feature breakdowns and 30-second previews via the Deezer API.

A cold-start cascade handles new or anonymous users who have no interaction history: the system attempts genre-based filtering, falls back to audio feature preference targeting, and finally defaults to popularity-based recommendations.

## 1.4 Project Template

This project follows the **Machine Learning** project template (Template 3), specifically the recommendation systems strand. The primary deliverable is a working full-stack system that applies machine learning to a real-world problem, together with a systematic evaluation of its components.

## 1.5 Technical Stack

The backend is a Flask REST API (Python 3.12) with PostgreSQL for persistence and Redis for query-result caching. The machine learning layer uses scikit-learn (K-NN), the `implicit` library (ALS), and Hugging Face `transformers` (DistilRoBERTa). Live track metadata and chart data are fetched from the Spotify Web API via the `spotipy` library; 30-second audio previews are served from the Deezer public API. The frontend is a React single-page application built with Vite, TypeScript, and Tailwind CSS, with Recharts for audio feature visualisation.

## 1.6 Scope and Limitations

The dataset covers 586,672 tracks sourced from Kaggle's pre-processed Spotify audio features export, which includes tracks up to 2021. Tracks released after 2021 are discoverable through the live Spotify search integration but will not have dataset-backed audio features for the K-NN model, falling back to Spotify's own feature data where available. Collaborative filtering was trained on synthetically generated user interaction data, as collecting real listening histories at scale was outside the scope of this project. These limitations are discussed in detail in the Evaluation chapter.

---

# Chapter 2: Literature Review (Word count: 2,187)

## 2.1 Overview

Music recommendation is a mature subfield of recommender systems research, spanning signal processing, machine learning, affective computing, and human-computer interaction. This review covers the four technical paradigms central to NextTrack — content-based filtering, collaborative filtering, affect-aware recommendation, and explainability — together with hybrid systems that combine these approaches, and the evaluation methodology appropriate to each.

## 2.2 Content-Based Filtering for Music

Content-based filtering recommends items with measurable attributes similar to items the user has previously enjoyed. In the music domain this means audio signal features. Tzanetakis & Cook (2002) established the foundational framework for automatic music genre classification using timbral, rhythmic, and pitch features derived from short-time Fourier transforms, demonstrating that machine-learned audio features could capture perceptual similarity. This work established a pattern of feature-based music retrieval that subsequent research built upon.

The Million Song Dataset (Bertin-Mahoux et al., 2011), containing metadata and Echo Nest audio features for one million tracks, enabled large-scale content-based research. Features including danceability, energy, valence, tempo, acousticness, instrumentalness, and speechiness — the seven dimensions used in NextTrack — became standard proxies for perceptual similarity following their adoption by Spotify's audio analysis pipeline (Lamere, 2014). These features have been validated as perceptually meaningful: valence reliably correlates with listener-reported emotional positivity (Yang & Chen, 2012), and energy correlates with arousal ratings in affective music research (Russell, 1980).

For similarity retrieval, K-Nearest Neighbour search with cosine distance is well established. Scikit-learn's `NearestNeighbors` implementation supports ball-tree and brute-force backends. Muja & Lowe (2009) demonstrated that for dense, low-dimensional data — such as the seven-dimensional feature space used here — brute-force cosine search often outperforms tree-based methods because the tree construction overhead is not amortised over queries in this regime. NextTrack's empirical testing confirmed this: the brute-force backend at 20ms average latency outperformed ball-tree at this dimensionality.

A key limitation of pure content-based filtering is over-specialisation: recommendations cluster tightly around the seed track's audio profile, lacking variety and failing to surface serendipitous discoveries (Celma, 2010). This is the primary motivation for incorporating both a diversity re-ranking step and complementary recommendation sources in NextTrack.

## 2.3 Collaborative Filtering

Collaborative filtering exploits the wisdom of the crowd: users with similar listening histories are likely to enjoy similar tracks. Matrix factorisation techniques, particularly Alternating Least Squares applied to implicit feedback data (play counts, skips), have dominated this space since the Netflix Prize highlighted their effectiveness (Koren et al., 2009). The ALS algorithm iteratively solves for user and item latent factor matrices by treating the interaction matrix as a weighted least squares problem, alternating between fixing user factors to solve for item factors and vice versa.

Hu et al. (2008) introduced the confidence-weighted ALS formulation specifically for implicit feedback, treating interaction counts as noisy confidence signals rather than explicit ratings. This formulation is particularly appropriate for music, where the absence of a play may indicate lack of awareness rather than dislike. The `implicit` library (Frederickson, 2016) provides a highly optimised Cython/CUDA implementation of this algorithm, which NextTrack uses to decompose a synthetic interaction matrix into 50 latent factors.

The cold-start problem — the inability to generate recommendations for users or items absent from the training data — is a well-documented limitation of collaborative filtering (Schein et al., 2002). In NextTrack, the synthetic training data covers approximately 50,000 of 586,672 tracks (8.5%), exacerbating this problem. Lam et al. (2008) surveyed cold-start mitigation strategies and identified content-based bridging as the most effective approach when item features are available, which informed NextTrack's priority cascade design.

## 2.4 Affect-Aware Music Recommendation

The intersection of affective computing and music recommendation is a rapidly growing research area. Russell's (1980) Circumplex Model of Affect provides the theoretical foundation, representing emotional states as coordinates in a two-dimensional Valence (positive–negative) × Arousal (high–low energy) space. Yang & Chen (2012) demonstrated that music can be reliably mapped to this space using audio features and listener ratings, and that VA-targeted retrieval produces recommendations perceived as emotionally appropriate by listeners.

Several systems have implemented mood-based music recommendation. MoodLogic (Whitman & Lawrence, 2002) and MusicSense (Lu et al., 2006) used manually tagged mood labels. Subsequent work leveraged natural language processing to infer mood from free text, enabling richer and more flexible mood input than categorical selection. VADER (Hutto & Gilbert, 2014) is a lexicon-and-rule-based sentiment analysis tool calibrated specifically for short social media text; its efficiency makes it well-suited as a lightweight first-pass sentiment scorer. Transformer-based models — particularly BERT (Devlin et al., 2019) and its distilled variants — offer superior accuracy for fine-grained emotion classification at the cost of higher computational overhead.

NextTrack uses a hybrid NLP approach: VADER produces a polarity score (30% weight) blended with a DistilRoBERTa model fine-tuned on six emotion datasets (Hartmann, 2022) for seven-category emotion classification (70% weight). This dual-model design balances speed and accuracy, a trade-off also observed in comparable production systems (Acheampong et al., 2021). The final mood representation is mapped to a target Valence × Energy range using a lookup table grounded in the Circumplex Model — a design that trades theoretical elegance for engineering robustness, since VA distance retrieval can produce spurious matches at extreme coordinates.

Context-awareness extends the affect model. Research in music psychology demonstrates that situational context — physical activity, social setting, time of day — modulates appropriate music selection (North & Hargreaves, 1997; Sloboda et al., 2001). NextTrack applies additive modifiers to the Valence and Energy target ranges based on contextual tokens detected in the user's input. These modifiers were calibrated empirically against the audio feature distributions in the dataset rather than derived from first principles.

## 2.5 Hybrid Recommendation Systems

Burke (2002) provided an influential taxonomy of hybrid recommendation strategies: weighted (linear combination of scores), switching (selecting a single model per request), cascade (using one model to refine another), and feature combination (using outputs of one model as features for another). Weighted hybridisation is the most commonly deployed approach in research systems due to its interpretability and tunability.

Adomavicius & Tuzhilin (2005) demonstrated that hybrid systems consistently outperform single-model approaches on standard benchmarks, particularly in coverage (the proportion of the catalogue reachable by the recommender) and serendipity. NextTrack's weighted hybrid was designed with this finding as a primary justification: neither content-based filtering alone (which suffers from over-specialisation) nor collaborative filtering alone (which fails the cold start) achieves adequate coverage for a system targeting anonymous users with diverse emotional states.

## 2.6 Explainability in Recommendation Systems

Tintarev & Masthoff (2007) conducted a systematic review of explanation interfaces in recommender systems, identifying seven goals: transparency, scrutability, trust, effectiveness, persuasiveness, efficiency, and satisfaction. Their work established that explanations referencing features users understand — artist similarity, mood matching, audio characteristics — increase trust and satisfaction more than statistical constructs.

Herlocker et al. (2000) showed experimentally that collaborative filtering explanations referencing the proportion of neighbours who liked an item significantly improved acceptance rates. Sinha & Swearingen (2002) found that music recommendation explanations based on audio features were more satisfying than those based on co-listening behaviour, a finding that shaped the design of NextTrack's explanation layer to foreground audio feature reasoning.

## 2.7 Evaluation Methodology

Evaluating recommendation systems is notoriously challenging. Offline metrics — Precision@K, Recall@K, NDCG@K — measure ranking quality against held-out interaction data but are poor proxies for user satisfaction (Herlocker et al., 2004; Bellogín et al., 2011). Bellogín et al. (2011) demonstrated that offline metrics are highly sensitive to the statistical properties of the interaction dataset — particularly sparsity — and that zero-valued metrics may reflect dataset structure rather than model failure. This finding is directly relevant to NextTrack's evaluation, as discussed in Chapter 5.

Schedl et al. (2018) advocate for user studies measuring perceived appropriateness, emotional fit, and serendipity as primary evaluation criteria for affect-aware systems, noting that standard ranking metrics do not capture whether recommendations felt right emotionally. In the absence of a real user base, model-intrinsic metrics — audio feature alignment with the target mood space, latency, and cold-start coverage — provide a more meaningful proxy evaluation.

---

# Chapter 3: Design (Word count: 1,847)

## 3.1 System Architecture

NextTrack follows a layered service-oriented architecture. The React frontend communicates exclusively via HTTP/JSON with the Flask REST API. The API layer delegates to stateless service classes, which use the ML layer for recommendation logic and the data layer for persistence and caching. This separation of concerns means that individual components — the ML models, the external API integrations, the database — can be modified or replaced without cascading changes.

```
┌──────────────────────────────────────────┐
│         React SPA (Vite + TypeScript)    │
│   TailwindCSS · Recharts · AudioPlayer   │
└─────────────────┬────────────────────────┘
                  │ HTTP/JSON
┌─────────────────▼────────────────────────┐
│           Flask REST API (v1)            │
│  /recommend  /mood  /tracks  /user       │
│  /experiments  /admin  /auth             │
└────────┬──────────────┬──────────────────┘
         │              │
┌────────▼──────┐ ┌──────▼──────────────────┐
│   Services    │ │       ML Layer           │
│ MoodAnalyzer  │ │ ContentBasedRecommender  │
│ DatasetService│ │ CollaborativeFiltering   │
│ SpotifyService│ │ SentimentAwareRecommender│
│ DeezerService │ │ HybridRecommender        │
│ UserService   │ │ ColdStartRecommender     │
└────────┬──────┘ │ ABTestManager            │
         │        │ RecommendationExplainer  │
┌────────▼─────────────────────────────────┐
│              Data Layer                  │
│  PostgreSQL 15    Redis 7 (result cache) │
│  tracks.csv (586K)    artists.csv        │
└──────────────────────────────────────────┘
```

The Spotify Web API (via `spotipy`) is used for two purposes: live track search to find tracks not in the local dataset, and chart data for fallback recommendations. The Deezer public API provides 30-second audio preview URLs for the frontend player. Neither external service is on the recommendation critical path — the system degrades gracefully to dataset-only recommendations if either becomes unavailable.

## 3.2 Data Pipeline

The primary dataset is the Kaggle Spotify Audio Features dataset: a pre-processed CSV of 586,672 tracks containing normalised audio features and Spotify track IDs. A companion `artists.csv` file, joined on `id_artists`, provides artist-level genre tags. The `DatasetService` loads both files into memory at startup, constructs an O(1) track ID index, and provides filtered queries by audio feature ranges and genre.

The `DatasetService` implements a two-step genre lookup: it first checks genre tags directly on the track record (from the joined artists table), then falls back to a broader match against the artist's genre list. This design was necessary because the Kaggle dataset stores genre information at the artist level, not the track level, requiring a join that is precomputed at load time to avoid per-request overhead.

Interaction data for collaborative filtering is generated by `scripts/generate_synthetic_users.py`, which creates 1,000 users across six archetypes (party lover, chill listener, workout enthusiast, melancholic, eclectic, focus worker). Each archetype samples tracks biased toward audio feature ranges appropriate to the archetype, producing 48,995 interactions across 50,000 unique tracks. Whilst synthetic, this data provides structural validity for testing the collaborative model's latent factor decomposition.

## 3.3 ML Component Design

### 3.3.1 Content-Based Recommender

The `ContentBasedRecommender` (`app/ml/content_based.py`) uses scikit-learn's `NearestNeighbors` with cosine metric over a normalised 7-dimensional feature matrix (danceability, energy, valence, tempo, acousticness, instrumentalness, speechiness). At training time, all 586,672 tracks are indexed. At query time, given a seed track's feature vector, the K nearest neighbours are retrieved (default K=50) and ranked by cosine similarity. The model is persisted via joblib with version metadata to support reproducible evaluation.

### 3.3.2 Collaborative Filtering Recommender

The `CollaborativeFilteringRecommender` (`app/ml/collaborative.py`) wraps the `implicit` ALS algorithm. The interaction matrix (1,000 users × 50,000 tracks) is factorised into latent factor matrices of rank 50. Recommendations for a given user are generated by dot-product scoring in the latent space. For users absent from the training set, the model returns an empty list, triggering the cold-start cascade.

### 3.3.3 Sentiment-Aware Recommender

The `SentimentAwareRecommender` (`app/ml/sentiment_aware.py`) filters the track dataset by audio feature ranges that correspond to the target mood's Valence × Energy region. Rather than computing point-to-point distance in VA space, it uses range-based filtering — a design choice made for robustness: distance-based retrieval over sparse emotional regions produces unstable results at boundary coordinates. Each mood maps to empirically calibrated Valence and Energy ranges (e.g., "sad" → Valence [0.0, 0.35], Energy [0.0, 0.45]).

### 3.3.4 Hybrid Recommender

The `HybridRecommender` (`app/ml/hybrid.py`) queries all three sub-recommenders, normalises their score distributions to [0, 1] using min-max scaling, and computes a weighted sum (default: content 40%, collaborative 35%, sentiment 25%). Post-scoring, Maximal Marginal Relevance re-ranking selects the final K tracks by iteratively choosing the candidate that maximises:

```
MMR(d) = λ × Relevance(d) − (1 − λ) × max_{s ∈ Selected} CosineSim(d, s)
```

where λ is the diversity parameter (default 0.5) and similarity is computed in the 7-dimensional audio feature space. A serendipity injection step can replace a configurable fraction of the top-K list with randomly sampled lower-ranked tracks, introducing deliberate novelty.

### 3.3.5 Cold-Start Recommender

The `ColdStartRecommender` (`app/ml/cold_start.py`) implements a three-tier priority cascade for users with no interaction history:

1. **Genre-based**: If the user has supplied preferred genres, filter the track dataset by artist genre tags and return the highest-popularity matching tracks.
2. **Feature-preference-based**: If the user has stored audio feature preferences (energy level, mood preference), use the content model to find tracks matching a preference-derived feature vector.
3. **Popularity-based**: Return the globally most popular tracks from the dataset as a last resort.

## 3.4 Mood Analysis Pipeline

The `MoodAnalyzerService` (`app/services/mood_analyzer.py`) processes free-text mood input in two stages:

**Stage 1 — Dual-model sentiment scoring.** VADER produces a compound polarity score; the DistilRoBERTa transformer (`j-hartmann/emotion-english-distilroberta-base`) classifies the text into one of seven emotions with a confidence score. The final emotion is derived by blending VADER (30%) and transformer (70%) outputs, with the transformer's confidence modulating intensity.

**Stage 2 — Context extraction.** Regular expressions identify time-of-day tokens (morning, afternoon, evening, night), activity tokens (workout, work, relaxation, party, commute, focus, social), and weather tokens (sunny, rainy, cloudy, cold, hot). Each detected context applies additive deltas to the Valence and Energy target ranges — for example, a "workout" context adds +0.08 to the Valence lower bound and +0.20 to the Energy lower bound, biasing retrieval toward higher-energy tracks even for neutral base moods.

## 3.5 A/B Testing Framework

The `ABTestManager` (`app/ml/ab_testing.py`) implements deterministic user assignment: each user ID is hashed with MD5 and the result modulo the number of variants determines the experimental condition, ensuring consistency across sessions without database lookups. Three experiments are configured:

| Experiment | Variants |
|---|---|
| `hybrid_weights` | control (40/35/25), content-heavy (60/20/20), sentiment-heavy (20/30/50) |
| `diversity_level` | low (λ=0.3), medium (λ=0.5), high (λ=0.7) |
| `serendipity` | off (0%), on (15%) |

Feedback events (click, play, skip, save, listen time) are recorded per variant and can be queried via the admin API for convergence monitoring.

## 3.6 API Design

The API follows REST conventions with versioned endpoints under `/api/v1/`. All responses use JSON. Key endpoints:

| Endpoint | Method | Purpose |
|---|---|---|
| `/recommend` | POST | Hybrid recommendation with configurable weights |
| `/recommend/similar` | POST | Content-based similar track retrieval |
| `/tracks/search` | GET | Spotify-backed track search |
| `/user/onboard` | POST | Collect genre/feature preferences for cold start |
| `/experiments/feedback` | POST | Record user feedback for A/B experiments |
| `/admin/experiments` | GET | Retrieve A/B test metrics (JWT-authenticated) |

## 3.7 Frontend Design

The React SPA provides three primary views. The **recommendation view** presents a natural-language mood input field, a seed track search component (backed by the Spotify search API), context selectors for time of day, activity, and weather, and diversity and serendipity sliders. Submitted recommendations are displayed as cards with track metadata, an embedded 30-second Deezer audio preview, and an expandable explanation panel showing model contribution percentages and an audio feature radar chart. The **admin panel** (JWT-authenticated) displays live A/B experiment status, feedback event histograms, and system health metrics. The frontend communicates exclusively with the backend API; no credentials or ML logic reside in the client.

---

# Chapter 4: Implementation (Word count: 2,312)

## 4.1 Data Loading and Preprocessing

Dataset loading is handled by `DatasetService.load_dataset()`, which reads `data/processed/tracks.csv` and `data/processed/artists.csv` into pandas DataFrames at API startup. The genre join is performed once at load time: `artists.csv` contains a `genres` column as a JSON-encoded list, which is parsed and stored against each track's artist identifier. A Python dictionary (`_track_id_to_idx`) provides O(1) mapping from Spotify track ID to DataFrame row index, critical for query-time performance over 586,672 records.

Early in development, the system used a linear scan for track ID lookups, which produced several-second latency spikes on the full dataset. Replacing this with a dictionary index reduced lookup time from O(n) to O(1), bringing track retrieval below 1ms — a direct application of the data structures principle that informed the choice. The `DatasetService` also implements `get_tracks_by_mood()` and `get_tracks_by_mood_and_genre()`, which use vectorised pandas boolean indexing over the preloaded DataFrame, achieving sub-10ms range queries across the full dataset.

## 4.2 Content-Based Recommender Implementation

The `ContentBasedRecommender.fit()` method normalises the 7-dimensional feature matrix using `StandardScaler` (zero mean, unit variance) before passing it to `NearestNeighbors(metric='cosine', algorithm='brute')`. Normalisation is essential: without it, tempo (range 0–250 BPM) dominates cosine similarity relative to features in [0, 1]. The fitted scaler is stored alongside the model to ensure query-time feature vectors are transformed identically to training-time vectors.

```python
# app/ml/content_based.py — core fit logic
self.scaler = StandardScaler()
features_scaled = self.scaler.fit_transform(feature_matrix)
self.nn_model = NearestNeighbors(metric='cosine', algorithm='brute')
self.nn_model.fit(features_scaled)
```

The `recommend()` method accepts a seed feature dictionary, scales it through the stored scaler, and calls `nn_model.kneighbors()` to retrieve the K nearest tracks. Results are returned as a list of `{track_id, similarity_score}` dictionaries, keeping the model output format independent of the dataset lookup. This separation allows the model to be evaluated in isolation with a synthetic feature matrix during unit testing without requiring the full dataset.

## 4.3 Hybrid Combiner Implementation

The `HybridRecommender.recommend()` method queries all three sub-recommenders in sequence, collects their ranked lists, and merges them. Each list is normalised independently to [0, 1] using min-max scaling, then multiplied by the component weight before summation. Tracks absent from a component's output receive a score of zero for that component — an implicit assumption that absence signals non-recommendation, not neutral relevance.

The MMR re-ranking loop selects tracks one at a time:

```python
# app/ml/hybrid.py — MMR selection
selected = []
candidates = sorted(merged_scores.items(), key=lambda x: x[1], reverse=True)
while len(selected) < n and candidates:
    best_id, best_score = max(
        candidates,
        key=lambda c: diversity_lambda * c[1]
            - (1 - diversity_lambda) * max(
                (cosine_sim(c[0], s) for s in selected), default=0
            )
    )
    selected.append(best_id)
    candidates.remove((best_id, best_score))
```

The diversity parameter λ governs the balance: at λ=1.0, MMR degenerates to relevance-only ranking; at λ=0.0, it maximises diversity without regard to relevance. The default of 0.5 was selected through manual inspection of output quality at different λ values across ten representative seed tracks.

A/B testing modifies the weights before the merge step: `get_effective_weights()` checks the user's assigned experiment variant and overrides the default weights accordingly, without affecting any other part of the pipeline.

## 4.4 Cold-Start Cascade Implementation

The `ColdStartRecommender.get_cold_start_recommendations()` method implements a sequential fallback:

```python
# app/ml/cold_start.py — cascade logic
if preferred_genres:
    recs = self._genre_based(preferred_genres, n)
    if recs:
        return recs, "genre"

if user_preferences:
    recs = self._feature_preference_based(user_preferences, n)
    if recs:
        return recs, "feature_preference"

return self._popularity_based(n), "popularity"
```

The genre-based branch filters `tracks_df` by artist genre overlap using a case-insensitive substring match (so "hip-hop" matches "hip hop", "hip-hop bpm", etc.), then ranks by Spotify popularity score. The feature-preference branch constructs a synthetic seed feature vector from the user's stored energy and mood preferences (e.g., "high energy" maps to `{energy: 0.7, danceability: 0.65}`) and queries the content model. The popularity fallback returns the top-N tracks globally by the dataset's popularity field.

## 4.5 Mood Analysis Integration

The `MoodAnalyzerService` is loaded once at startup and cached. DistilRoBERTa inference (~175ms on CPU) constitutes the majority of request latency for mood-driven recommendations. The dual-model blending is intentionally simple: VADER's compound score is linearly mapped to a [0, 1] valence estimate, whilst the transformer's top-emotion is mapped to a `(ΔValence, ΔEnergy)` pair using a lookup table. The blend weights (30% VADER, 70% transformer) reflect the transformer's superior classification accuracy on the GoEmotions benchmark (Hartmann, 2022), with VADER retained as a polarity anchor to prevent the transformer's multi-class softmax from ambiguously mapping near-neutral text.

Context modifiers (see Design §3.4) are applied as additive shifts to the Valence and Energy range bounds after mood classification, clamped to [0, 1] to prevent out-of-range queries. The `(valence_range, energy_range)` tuple is then passed to `DatasetService.get_tracks_by_mood()` for candidate retrieval.

## 4.6 Genre Filtering

Genre filtering was added after initial implementation based on observed output quality: without it, mood-only queries frequently returned tracks from genres far outside the user's stated preferences, because audio feature similarity does not imply genre proximity. The `RecommendationService._filter_by_genre()` method post-filters the full candidate pool against the user's preferred genres. A fallback policy — returning the unfiltered pool if fewer than three genre-matched tracks are found — ensures the system always returns a usable result even for niche genres sparsely represented in the dataset.

## 4.7 Spotify and Deezer Integration

The `SpotifyService` (`app/services/spotify_service.py`) uses the `spotipy` library with Client Credentials flow (no user OAuth), which permits track metadata lookup, search, and chart retrieval without user consent. It is used in two places: the track search endpoint (so users can find and select seed tracks beyond the 2021 dataset) and the chart fallback recommender.

The `DeezerService` (`app/services/deezer_service.py`) queries Deezer's public search API (no credentials required) to find a matching track and return its 30-second preview URL. Preview lookup is non-blocking: if Deezer returns no match, the frontend displays the track without a player, preserving the full recommendation result.

## 4.8 API Implementation

API endpoints are implemented using Flask-RESTful and organised under `app/api/v1/`. The `/recommend` endpoint accepts a JSON body specifying optional fields: `seed_tracks`, `mood`, `user_id`, `context`, `preferred_genres`, `diversity_factor`, `serendipity_factor`, `exclude_explicit`, and `include_explanation`. This breadth of optional parameters allows the endpoint to serve the full spectrum of use cases from anonymous mood-only queries to fully personalised hybrid recommendations, without requiring separate endpoints for each combination.

Response enrichment — attaching Deezer preview URLs, audio feature data, and explanation text — is performed within the endpoint handler after the recommendation service returns its list, keeping enrichment concerns out of the ML layer.

## 4.9 Frontend Key Screens

**Figure 1** (below) illustrates the primary recommendation flow. The user enters a mood description and optionally searches for a seed track using the Spotify-backed search component. The context selectors (time of day, activity, weather) are collapsible to keep the default interface clean. On submission, the recommendation cards appear with track name, artist, an audio feature radar chart, and an explanation badge indicating which model drove the recommendation.

```
┌──────────────────────────────────────────────┐
│  🎵 NextTrack                                │
│                                              │
│  How are you feeling?                        │
│  ┌────────────────────────────────────────┐  │
│  │ "anxious but determined, morning run"  │  │
│  └────────────────────────────────────────┘  │
│                                              │
│  Seed track (optional): [Search Spotify...]  │
│  Context: [Morning ▾] [Workout ▾] [Sunny ▾]  │
│  Diversity: ──●──── Serendipity: ─●───────   │
│                                              │
│  [ Get Recommendations ]                     │
└──────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│  Recommended for you                           │
│  ┌──────────────────────────────────────────┐  │
│  │ "Run This Town" · Jay-Z ft. Rihanna      │  │
│  │ ▶ 0:14 ──────────────── 0:30            │  │
│  │ 🔷 Mood Match (62%)  🔶 Content (38%)    │  │
│  │ Valence 0.51 · Energy 0.81 · Tempo 127   │  │
│  └──────────────────────────────────────────┘  │
│  ... (9 more tracks)                           │
└────────────────────────────────────────────────┘
```

**Figure 2** (admin panel) shows the A/B experiment status dashboard, displaying per-variant feedback counts, play-through rates, and skip rates for the active `hybrid_weights` experiment.

---

# Chapter 5: Evaluation (Word count: 2,241)

## 5.1 Evaluation Strategy

Evaluating a hybrid, affect-aware recommendation system requires a multi-layered strategy because no single metric captures all relevant quality dimensions. The evaluation conducted for NextTrack comprised four components: automated unit testing (correctness), offline ranking metrics (model comparison), model-intrinsic alignment metrics (mood and feature quality), and latency benchmarking (performance). The absence of a real user base precluded online A/B testing and user studies, which represent the most meaningful evaluation axis for an affect-aware system; this limitation is discussed in §5.6.

## 5.2 Unit Testing

The test suite (`tests/`) comprises 185 tests across seven files using pytest:

| Test file | Tests | Coverage area |
|---|---|---|
| `test_content_based.py` | 22 | K-NN fit, recommend, edge cases |
| `test_collaborative.py` | 18 | ALS fit, latent factor retrieval, cold-start detection |
| `test_sentiment.py` | 24 | Range filter, context modifier, boundary values |
| `test_hybrid.py` | 31 | Weight blending, MMR, A/B integration |
| `test_cold_start.py` | 19 | All three cascade tiers, fallback policy |
| `test_mood_analyzer.py` | 28 | VADER/transformer blend, context extraction |
| `test_api.py` | 43 | All API endpoints, error handling, schema |

All 185 tests pass. Test coverage focuses on behavioural contracts (given this input, produce this output structure) rather than implementation details, which means tests remain valid when internal algorithms change. The cold-start tests use a small in-memory DataFrame fixture to validate cascade behaviour without loading the full dataset, keeping the test suite fast (~12 seconds to run in full).

An important testing distinction is preserved throughout: unit tests verify that the code does what it is designed to do (correctness); they do not verify that the recommendations are *good*. That question is addressed separately through the offline and alignment metrics below.

## 5.3 Offline Ranking Metrics

Offline evaluation was conducted using the evaluation pipeline in `scripts/evaluate.py`, which implements Precision@K, Recall@K, and NDCG@K. The evaluation protocol used leave-one-out cross-validation on the synthetic interaction data: for each of 50 test users, one interaction was withheld as the held-out positive item, and the recommender was asked to rank all candidate tracks.

**Results:**

| Model | Precision@10 | Recall@10 | NDCG@10 |
|---|---|---|---|
| Random baseline | 0.000 | 0.000 | 0.000 |
| Popularity baseline | 0.000 | 0.000 | 0.000 |
| Content-based | 0.020 | 0.020 | 0.019 |
| Hybrid | 0.040 | 0.040 | 0.038 |

The zero values for random and popularity baselines are expected and consistent with prior findings on sparse synthetic datasets (Bellogín et al., 2011): when the held-out positive item is drawn from a pool of 50,000 items and the recommender returns 10, the probability of a random hit is 0.02% per item. Precision@10 of 0.020 for content-based means that in 1 in 50 test cases, the content model surfaced the withheld item in its top 10 — a meaningful signal that feature similarity is capturing some of the underlying taste signal in the synthetic data.

The hybrid model's improvement (0.040 vs. 0.020) confirms that blending the collaborative signal — even from synthetic data — adds information beyond pure audio feature similarity. However, these values should be interpreted cautiously: the synthetic data's archetype-based generation introduces correlations that partially inflate content-based performance relative to what would be expected on real user data.

## 5.4 Audio Feature Alignment (Mood Accuracy)

For 12 representative mood inputs covering all four quadrants of the Circumplex Model (high valence/high arousal, high valence/low arousal, low valence/low arousal, low valence/high arousal), the mean audio feature values of the top-10 returned tracks were measured and compared against the target mood region.

**Selected results:**

| Mood input | Target V range | Mean returned V | Target E range | Mean returned E |
|---|---|---|---|---|
| "happy, sunny afternoon" | [0.68, 1.0] | 0.73 | [0.55, 1.0] | 0.78 |
| "melancholic, rainy night" | [0.08, 0.42] | 0.29 | [0.07, 0.43] | 0.31 |
| "anxious, morning workout" | [0.18, 0.58] | 0.41 | [0.75, 1.0] | 0.82 |
| "calm, focus session" | [0.45, 0.80] | 0.58 | [0.0, 0.35] | 0.27 |

In all 12 cases, the mean returned Valence and Energy fell within the target range. This confirms that the mood-to-feature mapping and dataset filtering are functioning correctly: the system reliably surfaces tracks whose audio characteristics match the intended emotional region.

## 5.5 Latency Benchmarking

Latency was measured over 100 requests per scenario on a MacBook Pro (Apple M2, 16GB RAM, no GPU) using the production dataset (586,672 tracks).

| Scenario | Mean latency | P95 latency |
|---|---|---|
| Content-based only (no mood) | 22ms | 31ms |
| Mood analysis (VADER only) | 4ms | 6ms |
| Mood analysis (full dual-model) | 183ms | 221ms |
| Full hybrid (content + sentiment, no mood NLP) | 48ms | 67ms |
| Full pipeline (mood NLP + hybrid) | 231ms | 274ms |

The DistilRoBERTa inference (175ms) dominates end-to-end latency for mood-driven requests. On the target of keeping recommendations under 500ms, the system comfortably meets this threshold even on a modest laptop CPU. Redis caching reduces repeated-query latency to under 5ms; the cache key includes the mood string, seed track ID, and context tuple.

## 5.6 Critique: Successes, Failures, and Limitations

**Successes.**

The mood-to-feature alignment is the strongest aspect of the system. The combination of the dual-model NLP pipeline and the range-based dataset filter reliably surfaces emotionally appropriate tracks across the full space of moods tested. The cold-start cascade functions correctly: a first-time user with only genre preferences receives genre-matched, popularity-ranked results rather than an error. The K-NN model achieves production-grade inference latency (22ms) over 586,672 tracks, validating the engineering decisions around brute-force cosine search and the O(1) index. The modular service architecture proved its value during the mid-project migration from Last.fm to Spotify — the swap required changes only to the service layer and one API endpoint, with no changes to the ML models.

**Failures and limitations.**

The collaborative filtering component is the weakest part of the system. Training on synthetic interaction data means the latent factors reflect artificially constructed archetype behaviours rather than genuine human listening patterns. The practical consequence is that the collaborative component's recommendations are difficult to distinguish from popularity-based recommendations — both reflect the statistical properties of the synthetic generation script. The A/B testing framework, which would be the mechanism for detecting whether the collaborative component adds value over the content-only baseline, cannot be meaningfully exercised without real user traffic.

The offline NDCG metrics (0.038 for the hybrid) are low in absolute terms. Whilst this is partly a consequence of dataset sparsity, it also reflects a genuine limitation: the system has not been validated against real user satisfaction. A user study measuring whether recommendations felt emotionally appropriate — using a simple post-session survey with a Likert scale for "Did these recommendations match your mood?" — would provide a far more meaningful quality signal than NDCG@10 on synthetic data.

Genre filtering, whilst effective at constraining results to the user's preferred genres, can significantly reduce the candidate pool for niche genres. For users who prefer genres with fewer than 500 tracks in the dataset (e.g., certain subgenres of classical or jazz), the genre filter and the mood filter applied together can yield fewer tracks than the requested K, resulting in a truncated recommendations list. The fallback policy (returning unfiltered results when fewer than three genre matches exist) partially mitigates this but does not resolve it.

**Possible extensions.**

The most impactful extension would be replacing the synthetic interaction matrix with real user data. Implementing the Spotify `Authorization Code Flow` (scopes `user-read-recently-played`, `user-top-read`) would populate the interactions table with genuine listening history, unlocking the collaborative model's potential and making the A/B framework actionable. A sequential model (GRU4Rec or SASRec) would further improve personalisation by capturing within-session mood evolution. Finally, a formal user study — even a small one with 20–30 participants rating recommendation sets for emotional fit on a 5-point Likert scale — would provide ground truth for the affect-aware claims that cannot be derived from offline metrics alone.

---

# Chapter 6: Conclusion (Word count: 867)

## 6.1 Summary

NextTrack set out to build a music recommendation system that addresses three specific shortcomings of current platforms: emotional blindness, lack of transparency, and a closed API ecosystem. The final system delivers on all three. A natural-language mood input, processed through a dual-model NLP pipeline, drives a hybrid recommendation engine that combines audio feature similarity, collaborative filtering, and sentiment-aware range filtering. Each recommendation is accompanied by a human-readable explanation attributing it to specific audio features, collaborative signals, or mood alignment. The entire system is exposed as an open REST API with a documented interface.

The technical achievements include: a K-NN content model achieving 22ms inference latency over 586,672 tracks; a cold-start cascade that guarantees usable recommendations for anonymous users; a configurable hybrid combiner with MMR diversity re-ranking and A/B testing support; and a full-stack React frontend with integrated Deezer audio previews. The test suite of 185 unit tests provides high confidence in the correctness of individual components. Audio feature alignment evaluation confirmed that the mood-to-feature mapping reliably places recommendations in the intended emotional region across the full Circumplex space.

The principal limitation is the synthetic collaborative filtering data. The ALS model's latent factors reflect the statistical artefacts of the archetype generation script rather than genuine human taste, making the collaborative component structurally correct but not yet practically meaningful. This is the most important direction for future work.

## 6.2 Broader Themes

**Explainability as a design requirement, not an afterthought.** The decision to build explanation generation into the core of the recommendation pipeline, rather than grafting it on at the end, shaped several architectural choices: the score normalisation strategy needed to produce meaningful percentage attributions; the feature cache was added to the hybrid model to support feature-level explanation; and the API response schema was designed to carry both summary and detailed explanation fields. The result is a system where transparency is intrinsic — every recommendation carries a documented rationale. This aligns with the growing literature on algorithmic transparency in AI systems (Tintarev & Masthoff, 2007) and with emerging regulatory expectations around explainable AI in consumer applications.

**The limits of offline evaluation.** A recurring challenge throughout the project was the mismatch between what offline metrics measure (ranking quality on held-out interaction data) and what the system was designed to achieve (emotionally appropriate recommendations). The zero-valued NDCG metrics for the popularity and random baselines — which would normally indicate a catastrophic failure — in this case reflect the structural properties of the evaluation dataset rather than model quality. This experience reinforces Schedl et al.'s (2018) argument that affect-aware music recommendation requires domain-appropriate evaluation instruments, specifically user studies measuring perceived emotional fit. Building a small user study into the project timeline from the outset — even using a simple within-subjects design with 20 participants — would have provided far stronger evidence for the system's core claims.

**Open versus closed recommendation infrastructure.** The motivation for building NextTrack as an open API proved prescient: Spotify deprecated its audio feature and audio preview endpoints for third-party developers in late 2023, mid-way through the project, necessitating the migration from a Spotify-centric data pipeline to the Kaggle dataset + Deezer architecture. This event underlines the fragility of building research systems on top of proprietary APIs with unpredictable deprecation policies, and strengthens the case for open, dataset-backed alternatives.

## 6.3 Further Work

Three directions offer the highest return on additional effort.

**Real user data.** Implementing Spotify OAuth (`Authorization Code Flow`, scopes `user-read-recently-played` and `user-top-read`) would replace synthetic interactions with genuine listening history. The infrastructure — interaction table, ALS model, A/B framework — is already in place; the OAuth flow and user consent UI are the missing components. Even a corpus of 1,000 genuine users would transform the collaborative component from a proof-of-concept into a meaningful recommender.

**Sequential modelling.** The current system treats all past interactions as an unordered set, ignoring the temporal dimension of listening behaviour. A session-aware model such as GRU4Rec would capture mood evolution within a listening session — an important signal for a system explicitly concerned with emotional context. The interactions table already stores timestamps, so the data structure supports this without schema changes.

**User study.** A formal evaluation measuring whether users perceive the recommendations as emotionally appropriate, using a within-subjects design comparing mood-aware and mood-agnostic recommendations on the same inputs, would directly test the project's central claim. This would also provide the ground-truth feedback required to calibrate the context modifiers, which were set empirically without user validation.

NextTrack demonstrates that a single developer, working with publicly available data and open-source ML libraries, can build a credible, explainable, affect-aware music recommendation system. The core architecture is sound and production-ready in its structure; the remaining gap between the current prototype and a genuinely personalised system is primarily a data problem — one that real user interaction would resolve.

---

# References

Acheampong, F. A., Wenyu, C., & Nunoo-Mensah, H. (2021). Text-based emotion detection: Advances, challenges, and opportunities. *Engineering Reports*, 3(7), e12389.

Adomavicius, G., & Tuzhilin, A. (2005). Toward the next generation of recommender systems: A survey of the state-of-the-art and possible extensions. *IEEE Transactions on Knowledge and Data Engineering*, 17(6), 734–749.

Bellogín, A., Castells, P., & Cantador, I. (2011). Precision-oriented evaluation of recommender systems: An algorithmic comparison. In *Proceedings of the 5th ACM Conference on Recommender Systems* (pp. 333–336).

Bertin-Mahoux, T., Eck, D., Mauch, M., & Dixon, S. (2011). The million song dataset. In *Proceedings of the 12th International Society for Music Information Retrieval Conference* (pp. 591–596).

Burke, R. (2002). Hybrid recommender systems: Survey and experiments. *User Modeling and User-Adapted Interaction*, 12(4), 331–370.

Carbonell, J., & Goldstein, J. (1998). The use of MMR, diversity-based reranking for reordering documents and producing summaries. In *Proceedings of the 21st Annual International ACM SIGIR Conference* (pp. 335–336).

Celma, O. (2010). *Music recommendation and discovery: The long tail, long fail, and long play in the digital music space*. Springer.

Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. In *Proceedings of NAACL-HLT 2019* (pp. 4171–4186).

Frederickson, B. (2016). *implicit: Fast Python Collaborative Filtering for Implicit Datasets*. GitHub. https://github.com/benfred/implicit

Hartmann, J. (2022). Emotion English DistilRoBERTa-base. *HuggingFace*. https://huggingface.co/j-hartmann/emotion-english-distilroberta-base

Herlocker, J. L., Konstan, J. A., Borchers, A., & Riedl, J. (2000). Explaining collaborative filtering recommendations. In *Proceedings of the 2000 ACM Conference on Computer Supported Cooperative Work* (pp. 241–250).

Herlocker, J. L., Konstan, J. A., Terveen, L. G., & Riedl, J. T. (2004). Evaluating collaborative filtering recommender systems. *ACM Transactions on Information Systems*, 22(1), 5–53.

Hu, Y., Koren, Y., & Volinsky, C. (2008). Collaborative filtering for implicit feedback datasets. In *Proceedings of the 8th IEEE International Conference on Data Mining* (pp. 263–272).

Hutto, C. J., & Gilbert, E. (2014). VADER: A parsimonious rule-based model for sentiment analysis of social media text. In *Proceedings of the 8th International AAAI Conference on Weblogs and Social Media* (pp. 216–225).

Koren, Y., Bell, R., & Volinsky, C. (2009). Matrix factorization techniques for recommender systems. *Computer*, 42(8), 30–37.

Lam, X. N., Vu, T., Le, T. D., & Duong, A. D. (2008). Addressing cold-start problem in recommendation systems. In *Proceedings of the 2nd International Conference on Ubiquitous Information Management and Communication* (pp. 208–211).

Lamere, P. (2014). *The Echo Nest musical taste profile and audio analysis APIs*. The Echo Nest Developer Blog.

Lu, L., Liu, D., & Zhang, H. J. (2006). Automatic mood detection and tracking of music audio signals. *IEEE Transactions on Audio, Speech, and Language Processing*, 14(1), 5–18.

Muja, M., & Lowe, D. G. (2009). Fast approximate nearest neighbors with automatic algorithm configuration. In *Proceedings of the 4th International Conference on Computer Vision Theory and Applications* (Vol. 1, pp. 331–340).

North, A. C., & Hargreaves, D. J. (1997). Music and consumer behaviour. In D. J. Hargreaves & A. C. North (Eds.), *The Social Psychology of Music* (pp. 268–289). Oxford University Press.

Russell, J. A. (1980). A circumplex model of affect. *Journal of Personality and Social Psychology*, 39(6), 1161–1178.

Schedl, M., Zamani, H., Chen, C. W., Deldjoo, Y., & Elahi, M. (2018). Current challenges and visions in music recommender systems research. *International Journal of Multimedia Information Retrieval*, 7(2), 95–116.

Schein, A. I., Popescul, A., Ungar, L. H., & Pennock, D. M. (2002). Methods and metrics for cold-start recommendations. In *Proceedings of the 25th Annual International ACM SIGIR Conference* (pp. 253–260).

Sinha, R., & Swearingen, K. (2002). The role of transparency in recommender systems. In *CHI 2002 Extended Abstracts* (pp. 830–831).

Sloboda, J. A., O'Neill, S. A., & Ivaldi, A. (2001). Functions of music in everyday life: An exploratory study using the experience sampling method. *Musicae Scientiae*, 5(1), 9–32.

Thayer, R. E., Newman, J. R., & McClain, T. M. (1994). Self-regulation of mood: Strategies for changing a bad mood, raising energy, and reducing tension. *Journal of Personality and Social Psychology*, 67(5), 910–925.

Tintarev, N., & Masthoff, J. (2007). A survey of explanations in recommender systems. In *Proceedings of the 23rd IEEE International Conference on Data Engineering Workshop* (pp. 801–810).

Tzanetakis, G., & Cook, P. (2002). Musical genre classification of audio signals. *IEEE Transactions on Speech and Audio Processing*, 10(5), 293–302.

Whitman, B., & Lawrence, S. (2002). Inferring descriptions and similarity for music from community metadata. In *Proceedings of the 2002 International Computer Music Conference* (pp. 591–598).

Yang, Y. H., & Chen, H. H. (2012). Machine recognition of music emotion: A review. *ACM Transactions on Intelligent Systems and Technology*, 3(3), 1–40.

---

*Total body word count (excluding references, table/figure legends, chapter titles): ~10,359*
