#get liked youtube videos from youtube
#create a playlist on spotify
#search spotify
#add to your playlist

import json
import requests
import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

import youtube_dl

from config import user_id, token

songs_info = {}

def get_liked_youtube_videos():
    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
# Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "CLIENT_SECRET_FILE.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_console()
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        myRating="like"
    )
    response = request.execute()

    for item in response["items"]:
        video_title = item["snippet"]["title"]
        youtube_url = "https://www.youtube.com/watch?v={}".format(item['id'])

        video = youtube_dl.YoutubeDL({'nocheckcertificate': True}).extract_info(youtube_url, download=False)

        song_name = video["track"]
        artist = video["artist"]

        songs_info[video_title] = {
            "youtube_url": youtube_url,
            "song_name": song_name,
            "artist": artist
        }
def get_spotify_uri(song, artist):
    query = "https://api.spotify.com/v1/search?q={}%20{}&type=track%2Cartist&market=US&limit=10&offset=5".format(song,artist)
    response = requests.get(
        query,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token)
        }
    )
    response_json = response.json()
    
    return response_json["tracks"]["items"][0]["uri"]

def create_playlist():
    request_body = json.dumps({
        "name": "YouTube Videos",
        "description": "Description is mine",
        "public": False
    })

    query = 'https://api.spotify.com/v1/users/{}/playlists'.format(user_id)

    response = requests.post(
        query,
        data=request_body,
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token)
        }
    )

    response_json = response.json()
    return response_json['id']

def add_song_to_playlist():
    get_liked_youtube_videos()

    uris = []
    for song, info in songs_info.items():
        spotify_url = get_spotify_uri(info["song_name"], info["artist"])
        uris.append(spotify_url)

    playlist_id = create_playlist()

    request_data = json.dumps(uris)
    query = "https://api.spotify.com/v1/playlists/{}/tracks".format(playlist_id)

    response = requests.post(
        query,
        data=request_data,
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer {}".format(token)
        }
    )

    response_json = response.json()

    return response_json

add_song_to_playlist()
