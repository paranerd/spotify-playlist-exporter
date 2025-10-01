
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd

# Replace with your Spotify API credentials
SPOTIPY_CLIENT_ID = 'CLIENT_ID'
SPOTIPY_CLIENT_SECRET = 'CLIENT_SECRET'
SPOTIPY_REDIRECT_URI = 'http://127.0.0.1:9090'

# Scope for accessing user's playlists and liked songs
SCOPE = 'playlist-read-private user-library-read'

def authenticate_spotify():
    """Authenticates with Spotify and returns a spotipy object."""
    auth_manager = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE,
        open_browser=False
    )

    auth_url = auth_manager.get_authorize_url()
    print(f"Please go to this URL and authorize the app: {auth_url}")

    redirected_url = input("Paste the URL you were redirected to: ")

    code = auth_manager.parse_response_code(redirected_url)
    auth_manager.get_access_token(code, as_dict=False)

    sp = spotipy.Spotify(auth_manager=auth_manager)
    return sp

def get_all_playlists(sp):
    """Fetches all of the current user's playlists."""
    playlists = []
    results = sp.current_user_playlists(limit=50)
    playlists.extend(results['items'])

    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])

    return playlists

def get_playlist_tracks(sp, playlist_id):
    """Fetches all tracks from a given playlist."""
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks

def get_liked_songs_tracks(sp):
    """Fetches all of the user's liked songs."""
    results = sp.current_user_saved_tracks(limit=50)
    tracks = results['items']
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
    return tracks


def export_tracks_to_csv(tracks, filename):
    """Exports a list of tracks to a CSV file."""
    track_data = []
    for item in tracks:
        track = item['track']
        if track:
            track_data.append({
                'name': track.get('name'),
                'artists': ", ".join([artist['name'] for artist in track.get('artists', [])]),
                'album': track.get('album', {}).get('name'),
                'release_date': track.get('album', {}).get('release_date'),
                'duration_ms': track.get('duration_ms'),
                'popularity': track.get('popularity'),
                'isrc': track.get('external_ids', {}).get('isrc'),
                'external_url': track.get('external_urls', {}).get('spotify')
            })

    df = pd.DataFrame(track_data)
    df.to_csv(filename, index=False)
    print(f"Successfully exported {len(track_data)} tracks to {filename}")

if __name__ == '__main__':
    print("Authenticating with Spotify...")
    spotify = authenticate_spotify()

    print("Fetching your Spotify playlists...")
    all_playlists = get_all_playlists(spotify)

    # Add "Liked Songs" as the first option
    all_playlists.insert(0, {'name': 'Liked Songs', 'id': 'liked_songs'})


    if all_playlists:
        print("\nYour playlists:")
        for i, playlist in enumerate(all_playlists):
            print(f"{i + 1}: {playlist['name']}")

        while True:
            try:
                choice = int(input("\nEnter the number of the playlist you want to export: "))
                if 1 <= choice <= len(all_playlists):
                    selected_playlist = all_playlists[choice - 1]
                    break
                else:
                    print("Invalid number. Please try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

        playlist_id = selected_playlist['id']
        playlist_name = selected_playlist['name']

        print(f"\nFetching tracks for '{playlist_name}'...")
        if playlist_id == 'liked_songs':
            playlist_tracks = get_liked_songs_tracks(spotify)
        else:
            playlist_tracks = get_playlist_tracks(spotify, playlist_id)

        if playlist_tracks:
            # Sanitize playlist name for filename
            safe_playlist_name = "".join([c for c in playlist_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            filename = f"{safe_playlist_name.replace(' ', '_').lower()}.csv"
            export_tracks_to_csv(playlist_tracks, filename)
