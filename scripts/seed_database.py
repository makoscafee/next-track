#!/usr/bin/env python
"""
Script to seed the database with initial data
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import Interaction, Track, User


def seed_sample_tracks():
    """Seed database with sample tracks."""
    sample_tracks = [
        {
            "spotify_id": "4iV5W9uYEdYUVa79Axb7Rh",
            "name": "Blinding Lights",
            "artist": "The Weeknd",
            "album": "After Hours",
            "danceability": 0.514,
            "energy": 0.730,
            "valence": 0.334,
            "tempo": 171.005,
            "acousticness": 0.00146,
            "instrumentalness": 0.0000954,
            "speechiness": 0.0598,
            "popularity": 87,
        },
        {
            "spotify_id": "6UelLqGlWMcVH1E5c4H7lY",
            "name": "Watermelon Sugar",
            "artist": "Harry Styles",
            "album": "Fine Line",
            "danceability": 0.548,
            "energy": 0.816,
            "valence": 0.557,
            "tempo": 95.390,
            "acousticness": 0.122,
            "instrumentalness": 0,
            "speechiness": 0.0465,
            "popularity": 85,
        },
        {
            "spotify_id": "39LLxExYz6ewLAcYrzQQyP",
            "name": "Levitating",
            "artist": "Dua Lipa",
            "album": "Future Nostalgia",
            "danceability": 0.702,
            "energy": 0.825,
            "valence": 0.915,
            "tempo": 102.977,
            "acousticness": 0.00883,
            "instrumentalness": 0,
            "speechiness": 0.0601,
            "popularity": 88,
        },
    ]

    for track_data in sample_tracks:
        existing = Track.query.filter_by(spotify_id=track_data["spotify_id"]).first()
        if not existing:
            track = Track(**track_data)
            db.session.add(track)
            print(f"Added track: {track_data['name']}")

    db.session.commit()


def seed_sample_user():
    """Seed database with a sample user."""
    user = User.query.filter_by(external_id="demo_user").first()
    if not user:
        user = User(
            external_id="demo_user",
            username="Demo User",
            preferred_genres=["pop", "electronic"],
            preferred_valence=0.6,
            preferred_energy=0.7,
        )
        db.session.add(user)
        db.session.commit()
        print("Added demo user")


def main():
    """Main function to seed the database."""
    app = create_app("development")

    with app.app_context():
        # Create tables
        db.create_all()
        print("Database tables created")

        # Seed data
        seed_sample_tracks()
        seed_sample_user()

        print("Database seeding complete!")


if __name__ == "__main__":
    main()
