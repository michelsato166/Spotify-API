import os
import re
from yt_dlp import YoutubeDL
from youtubesearchpython import VideosSearch
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

CLIENT_ID = "7e80d59a712241e19354bf1937cc9139"
CLIENT_SECRET = "ebc64fa694a94f4dacb5b6a6c96c6033"

def init_spotify():
    auth_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
    return spotipy.Spotify(auth_manager=auth_manager)

def extract_playlist_id(playlist_url):
    match = re.search(r"(playlist\/|playlist:)([a-zA-Z0-9]+)", playlist_url)
    if not match:
        print("Invalid Spotify playlist URL.")
        return
    return match.group(2)

def get_playlist_metadata(spotify, playlist_id):
    try:
        return spotify.playlist(playlist_id)
    except Exception as e:
        print(f"Could not fetch playlist: {e}")
        return

def get_playlist_tracks(spotify, playlist_id):
    tracks = []
    results = spotify.playlist_tracks(playlist_id)
    while results:
        for item in results['items']:
            track = item['track']
            if not track: continue
            name = track['name']
            artists = ', '.join(artist['name'] for artist in track['artists'])
            full_title = f"{name} by {artists}"
            tracks.append(full_title)
        if results['next']:
            results = spotify.next(results)
        else:
            results = None
    return tracks

def search_youtube(query):
    search = VideosSearch(query, limit=1)
    results = search.result()['result']
    if results:
        return results[0]['link']
    return None

def download_audio(youtube_url, filename, download_dir):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(download_dir, f"{filename}.%(ext)s"),
        'quiet': True,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }
    with YoutubeDL(ydl_opts) as ydl:
        try:
            ydl.download([youtube_url])
        except Exception as e:
            print(f"Failed to download {filename}: {e}")

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', '', name)

def main():
    print("Spotify Playlist Downloader (via URL)\n")

    playlist_url = input("Paste Spotify playlist URL: ").strip()
    if not playlist_url:
        print("No URL provided.")
        return

    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    download_dir = os.path.join(desktop_path, "spotify_downloaded_playlist")
    os.makedirs(download_dir, exist_ok=True)

    spotify = init_spotify()

    playlist_id = extract_playlist_id(playlist_url)
    playlist = get_playlist_metadata(spotify, playlist_id)
    if not playlist:
        return

    print(f"\nPlaylist: {playlist['name']} by {playlist['owner']['display_name']}")

    tracks = get_playlist_tracks(spotify, playlist_id)
    print(f"Found {len(tracks)} tracks. Starting download...\n")

    for idx, track in enumerate(tracks, 1):
        print(f"[{idx}/{len(tracks)}] Searching YouTube for: {track}")
        youtube_url = search_youtube(track)
        if youtube_url:
            filename = sanitize_filename(track)
            print(f"Downloading: {filename}")
            download_audio(youtube_url, filename, download_dir)
        else:
            print("No YouTube result found.")

    print(f"All done! MP3s saved in: {os.path.abspath(download_dir)}")

main()