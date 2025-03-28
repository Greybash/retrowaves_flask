from flask import Flask, render_template, request, redirect, session, url_for
import os
import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Prevents Tkinter backend issues

import matplotlib.pyplot as plt
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from config import Config  # Import Config class
import uuid
import numpy as np
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


load_dotenv()
app = Flask(__name__)
app.config.from_object(Config)  # Load configuration from config.py

app.secret_key = "e3f1c2a5d5e1f2e4c9b6a4c8d3f0b7e6a8d5c3b9f4e2a1c7d6f0b8e5a4c2d3f1"


def generate_unique_code():
    """
    Generates a unique login code for the user.
    """
    return str(uuid.uuid4())
def get_sp():
    u = generate_unique_code()
    cache_file = os.path.join(BASE_DIR, f"{u}.cache")
    session['cache_file'] = cache_file  # Store cache file name in session
    return SpotifyOAuth(
        client_id=os.getenv("CLIENT_ID"),
        client_secret=os.getenv("CLIENT_SECRET"),
        redirect_uri=os.getenv("REDIRECT_URI"),
        scope=os.getenv("SPOTIFY_SCOPE"),
        cache_path=cache_file
    )

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    session.clear()
    auth_url = get_sp().get_authorize_url()
    return redirect(auth_url)



@app.route("/logout", methods=["POST"])
def logout():
    """Logs the user out and deletes the cache file."""
    cache_file = session.get('cache_file', '')
    if os.path.exists(cache_file):
        os.remove(cache_file)
    session.clear()
    return redirect(url_for('home'))


@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    token_info = get_sp().get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('dashboard'))

@app.route("/profile")
def profile():
    token_info = session.get('token_info', {})
    if not token_info:
        return redirect(url_for('login'))

    headers = {"Authorization": f"Bearer {token_info['access_token']}"}
    user_data = requests.get("https://api.spotify.com/v1/me", headers=headers).json()

    username = user_data.get('display_name', 'Unknown User')
    profile_image = user_data.get('images', [])
    if profile_image:
        profile_image = profile_image[0].get('url', url_for('static', filename='profile.png'))
    else:
        profile_image = url_for('static', filename='profile.png')  # Use default image


    return render_template('profile.html', username=username, profile_image=profile_image)


@app.route('/dashboard')
def dashboard():
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for('login'))  # Redirect if not logged in

    headers = {"Authorization": f"Bearer {token_info['access_token']}"}
    user_data = requests.get("https://api.spotify.com/v1/me", headers=headers).json()

    username = user_data.get('display_name', 'Spotify User')  # Default if missing
    profile_image = user_data.get('images', [])
    if profile_image:
        profile_image = profile_image[0].get('url', url_for('static', filename='profile.png'))
    else:
        profile_image = url_for('static', filename='profile.png')  # Use default image
 

    return render_template('dashboard.html', username=username, profile_image=profile_image)


@app.route('/playlist-to-personality')
def playlist_to_personality():
    return render_template('playlist_to_personality.html')



  # Show selection form on GET

@app.route('/select-playlist')
def select_playlist():
    """Fetches user's playlists and renders them in a dropdown list."""
    playlists = get_user_playlists()

    if not playlists:
        return render_template('select_playlist.html', error="No playlists found.")

    return render_template('select_playlist.html', playlists=playlists)

@app.route("/whole-profile")  # Ensure this route matches the name in `url_for`
def whole_profile():

    """Analyze all playlists as a single dataset and generate a combined chart."""
    
    # Retrieve token from session
    token_info = session.get('token_info')
    if not token_info:
        return redirect(url_for("login"))

    sp = spotipy.Spotify(auth=token_info['access_token'])

    # Fetch all playlists
    playlists = get_user_playlists()
    if not playlists:
        return render_template('analyze_playlist.html', error="No playlists found.")

    all_tracks = []

    # Iterate over all playlists and get tracks
    for playlist in playlists:
        df_tracks = get_playlist_tracks_with_genres(playlist['id'])
        if isinstance(df_tracks, pd.DataFrame) and not df_tracks.empty:
            all_tracks.append(df_tracks)

    # Combine all playlist tracks into a single DataFrame
    if not all_tracks:
        return render_template('analyze_playlist.html', error="No tracks found in any playlists.")
    
    df_tracks = pd.concat(all_tracks, ignore_index=True)

    # Load dataset and mapping files
    base_dir = os.path.abspath(os.path.dirname(__file__))
    dataset_path = os.path.join(base_dir, "data", "dataset.csv")
    mapping_path = os.path.join(base_dir, "data", "mapping.csv")

    if not os.path.exists(dataset_path) or not os.path.exists(mapping_path):
        return render_template('analyze_playlist.html', error="Dataset files not found.")

    features_df = pd.read_csv(dataset_path)
    p_df = pd.read_csv(mapping_path)

    if features_df.empty or p_df.empty:
        return render_template('analyze_playlist.html', error="Dataset files are empty or incorrectly formatted.")

    # Map track genres
    df_tracks['track_id'] = df_tracks['track_id'].astype(str)
    features_df['track_id'] = features_df['track_id'].astype(str)
    genre_dict = dict(zip(features_df['track_id'], features_df['track_genre']))
    df_tracks['track_genre'] = df_tracks['track_id'].map(genre_dict).fillna("Unknown")

    # Calculate genre distribution
    genre_counts = df_tracks['track_genre'].value_counts(normalize=True) * 100
    genre_percentage_df = pd.DataFrame({'genre': genre_counts.index, 'percentage': genre_counts.values})

    # Define personality trait mapping
    trait_mapping = {
        'Extraversion': 'Extroverted',
        'Openness to Experience': 'Creative',
        'Conscientiousness': 'Hardworking',
        'Self-Esteem': 'Confident',
        'Neuroticism': 'Anxious',
        'Introversion': 'Introverted',
        'Agreeableness': 'Agreeable',
        'Low Self-Esteem': 'Low Self-Esteem',
        'Gentle': 'Gentle',
        'Assertive': 'Bold',
        'Emotionally Stable': 'Emotionally Stable',
        'Intellectual': 'Intellectual',
        'At Ease': 'Calm'
    }

    # Calculate personality traits
    user_personality = {trait: 0 for trait in trait_mapping.values()}
    p_df['Genre'] = p_df['Genre'].str.title()
    genre_percentage_df['genre'] = genre_percentage_df['genre'].str.title()

    for _, row in genre_percentage_df.iterrows():
        genre = row['genre']
        percentage = row['percentage']
        if genre in p_df['Genre'].values:
            genre_traits = p_df[p_df['Genre'] == genre].iloc[0, 1:]
            for trait, value in genre_traits.items():
                if pd.notna(value) and trait in trait_mapping:
                    user_personality[trait_mapping[trait]] += value * (percentage / 100)

    # Convert personality data to DataFrame and sort
    personality_df = pd.DataFrame(list(user_personality.items()), columns=['Trait', 'Score'])
    personality_df = personality_df.sort_values(by='Score', ascending=False)

    # Generate personality pie chart
    filtered_personality = {k: v for k, v in user_personality.items() if v > 0}
    chart_path = None

    if filtered_personality:
        plt.figure(figsize=(8, 8), facecolor='black')  # Black background
        ax = plt.gca()
        ax.set_facecolor('black')

        plt.pie(
            filtered_personality.values(),
            labels=filtered_personality.keys(),
            autopct='%1.1f%%',
            colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(filtered_personality))),
            textprops={'color': 'white'}  # White text
        )

        plt.title("Your Combined Personality Traits", color='white')  # White title
        plt.axis('equal')

        # Ensure `static/` folder exists
        static_dir = os.path.join(base_dir, 'static')
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)

        chart_path = os.path.join(static_dir, 'combined_personality_chart.png')
        plt.savefig(chart_path, facecolor='black')  # Save with black background
        plt.close()

        # Update chart URL for HTML rendering
        chart_url = "/static/combined_personality_chart.png"
        print(f"Chart saved at: {chart_url}")

    return render_template('whole_profile.html', personality_df=personality_df.to_html(), chart_url=chart_url)



@app.route('/analyze-playlist', methods=['GET', 'POST'])
def analyze_playlist_personality():
    

    #  Retrieve token from session
    token_info = session.get('token_info')
    if not token_info:
        
        return redirect(url_for("login"))

    sp = spotipy.Spotify(auth=token_info['access_token'])

    if request.method == 'POST':
        playlist_id = request.form.get('playlist_id')
        if not playlist_id:
            
            return render_template('select_playlist.html', error="Please select a playlist.")

        
        df_tracks = get_playlist_tracks_with_genres(playlist_id)

        #  Ensure df_tracks is a DataFrame
        if not isinstance(df_tracks, pd.DataFrame) or df_tracks.empty:
            
            return render_template('analyze_playlist.html', error="No tracks found in the selected playlist.")

       
        base_dir = os.path.abspath(os.path.dirname(__file__))  
        dataset_path = os.path.join(base_dir, "data", "dataset.csv")
        mapping_path = os.path.join(base_dir, "data", "mapping.csv")

        

        # Check if dataset files exist
        if not os.path.exists(dataset_path) or not os.path.exists(mapping_path):
            
            return render_template('analyze_playlist.html', error="Dataset files not found.")

        
        features_df = pd.read_csv(dataset_path)
        p_df = pd.read_csv(mapping_path)

        
        if features_df.empty or p_df.empty:
            
            return render_template('analyze_playlist.html', error="Dataset files are empty or incorrectly formatted.")

        # Convert track IDs to string before mapping
        df_tracks['track_id'] = df_tracks['track_id'].astype(str)
        features_df['track_id'] = features_df['track_id'].astype(str)

        #  Match track genres
        genre_dict = dict(zip(features_df['track_id'], features_df['track_genre']))
        df_tracks['track_genre'] = df_tracks['track_id'].map(genre_dict).fillna("Unknown")

        print(" Calculating genre distribution...")
        genre_counts = df_tracks['track_genre'].value_counts(normalize=True) * 100
        genre_percentage_df = pd.DataFrame({'genre': genre_counts.index, 'percentage': genre_counts.values})

        # Define personality trait mapping
        trait_mapping = {
            'Extraversion': 'Extroverted',
            'Openness to Experience': 'Creative',
            'Conscientiousness': 'Hardworking',
            'Self-Esteem': 'Confident',
            'Neuroticism': 'Anxious',
            'Introversion': 'Introverted',
            'Agreeableness': 'Agreeable',
            'Low Self-Esteem': 'Low Self-Esteem',
            'Gentle': 'Gentle',
            'Assertive': 'Bold',
            'Emotionally Stable': 'Emotionally Stable',
            'Intellectual': 'Intellectual',
            'At Ease': 'Calm'
        }

        # Calculate personality traits
        print(" Mapping genres to personality traits...")
        user_personality = {trait: 0 for trait in trait_mapping.values()}
        p_df['Genre'] = p_df['Genre'].str.title()
        genre_percentage_df['genre'] = genre_percentage_df['genre'].str.title()

        for _, row in genre_percentage_df.iterrows():
            genre = row['genre']
            percentage = row['percentage']
            if genre in p_df['Genre'].values:
                genre_traits = p_df[p_df['Genre'] == genre].iloc[0, 1:]
                for trait, value in genre_traits.items():
                    if pd.notna(value) and trait in trait_mapping:
                        user_personality[trait_mapping[trait]] += value * (percentage / 100)

        print(" Generating personality dataframe...")
        personality_df = pd.DataFrame(list(user_personality.items()), columns=['Trait', 'Score'])
        personality_df = personality_df.sort_values(by='Score', ascending=False)
        # Generate personality pie chart
        print("Creating personality chart...")
        filtered_personality = {k: v for k, v in user_personality.items() if v > 0}
        chart_path = None


        
        if filtered_personality:
            plt.figure(figsize=(8, 8), facecolor='black')  # Black background
            ax = plt.gca()
            ax.set_facecolor('black')

            plt.pie(
                filtered_personality.values(),
                labels=filtered_personality.keys(),
                autopct='%1.1f%%',
                
                colors = plt.cm.Greens(np.linspace(0.3, 0.9, len(filtered_personality))),
                textprops={'color': 'white'}  # White text
                )

            plt.title("Your Personality Traits Based on Your Playlist:", color='white')  # White title
            plt.axis('equal')

        # Ensure `static/` folder exists
            static_dir = os.path.join(base_dir, 'static')
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)

            chart_path = os.path.join(static_dir, 'combined_personality_chart.png')
            plt.savefig(chart_path, facecolor='black')  # Save with black background
            plt.close()

        # Update chart URL for HTML rendering
            chart_url = "/static/combined_personality_chart.png"
            print(f"Chart saved at: {chart_url}")

        

        print(" Rendering results.")
        return render_template('analyze_playlist.html', personality_df=personality_df.to_html(), chart_url=chart_url)

    # If GET request, just show the form
    playlists = get_user_playlists()
    return render_template('analyze_playlist.html', playlists=playlists)



def get_user_playlists():
    """Fetch the current user's playlists (handle pagination)."""
    token_info = session.get("token_info")
    if not token_info:
        print(" No token found. Redirecting to login.")
        return []

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        playlists = []
        limit = 50  # Max allowed limit per request
        offset = 0

        while True:
            response = sp.current_user_playlists(limit=limit, offset=offset)
            items = response.get('items', [])
            playlists.extend(items)

            

            # If less than 'limit' playlists are returned, we reached the end
            if len(items) < limit:
                break

            offset += limit  # Move to the next batch

        if not playlists:
            print(" No playlists found.")
            return []

        return [{'name': p['name'], 'id': p['id']} for p in playlists]

    except Exception as e:
        print(f" Error fetching playlists: {e}")
        return []


def get_playlist_id_by_name(playlist_name):
    """Find a playlist ID by name."""
    token_info = session.get("token_info")
    if not token_info:
        print("No token found. Redirecting to login.")
        return None

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        playlists = sp.current_user_playlists().get('items', [])

        for playlist in playlists:
            if playlist['name'].lower() == playlist_name.lower():
                return playlist['id']

        print(f" Playlist '{playlist_name}' not found.")
        return None

    except Exception as e:
        print(f" Error finding playlist: {e}")
        return None
def get_playlist_tracks_with_genres(playlist_id):
    """Retrieve tracks from a playlist and return as a DataFrame."""
    token_info = session.get("token_info")
    if not token_info:
        print(" No token found. Redirecting to login.")
        return pd.DataFrame()  #  Return an empty DataFrame instead of a list

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        tracks_data = sp.playlist_tracks(playlist_id).get('items', [])

        if not tracks_data:
            print(" No tracks found in the playlist.")
            return pd.DataFrame()  #  Return an empty DataFrame instead of a list

        track_details = []
        for track in tracks_data:
            if 'track' in track and track['track']:  # Ensure 'track' exists
                track_info = track['track']
                track_details.append({
                    'track_id': track_info['id'],
                    'track_name': track_info['name'],
                    'artist': track_info['artists'][0]['name'],
                    'album_name': track_info['album']['name'],
                    'popularity': track_info['popularity'],
                    'duration_ms': track_info['duration_ms'],
                    'explicit': track_info['explicit'],
                })

        return pd.DataFrame(track_details)  #  Convert list to Pandas DataFrame

    except Exception as e:
        print(f" Error fetching tracks: {e}")
        return pd.DataFrame()  #  Ensure it returns a DataFrame, not a list





if __name__ == '__main__':
    app.run(debug=True)
    from os import getenv
    app.run(host="0.0.0.0", port=int(getenv("PORT", 5000)))
