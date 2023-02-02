# Python310\lib\ssl.py, line 579 modified
from flask import Flask, request, url_for, session, redirect, render_template
from EjPiAj import *
import time
from pytube import  Search
import glob
import re
import ffmpy
import os
import eyed3
import requests
from PIL import Image


client_id = '' # Spotify API Client ID
client_secret = '' # Spotify API Client Secret
download_folder = 'downloads' # Path to download folder

app = Flask(__name__)

app.secret_key = "9kno8GliOHJ"
app.config['SESSION_COOKIE_NAME'] = 'Moj Kolacic'
TOKEN_INFO = "token_info"

# Home page
@app.route('/')
def home():
    """
    login to personal spotify
    """
    return render_template('home.html')

# Spotify login page
@app.route('/login')
def login():
    spotify = create_spotify_oauth()
    auth_url = spotify.get_authorize_url()
    return redirect(auth_url)

# Redirect page after login
@app.route('/redirect')
def redirectPage():
    """
    redirect to respond page with code
    """
    spotify = create_spotify_oauth()
    # clear seasion of previous data
    session.clear()
    code = request.args.get('code')
    # use code to access token
    token_info = spotify.get_access_token(code)
    #store token for later
    session[TOKEN_INFO] = token_info
    return redirect(url_for('getTracks', _external=True))

# Main app page
@app.route('/getTracks', methods = ['POST', 'GET'])
def getTracks():
    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect("/")
    spotify = Spotify(auth=token_info["access_token"])
    me = spotify.get_user_info()

    def search_playlist(name):
        playlists = spotify.get_playlists_by_user_id(me["id"])
        for elem in playlists:
            for val in elem.values():
                if val == name:
                    return elem['id']
    
    def search_on_spotify(name, type):
        return spotify.search(query=name, search_type=type)

    if request.method == 'POST':
        search_value = request.form['search-value']
        search_type = request.form['search-type']
    
        if search_type == 'playlist':
            playlist_id = search_playlist(search_value)
            try:
                playlist = spotify.get_playlist_tracks_by_id(playlist_id)
                return render_template('gettracks.html', data=me, playlist=playlist)
            except:
                raise Exception(f'Failed to find playlist: {search_value}!')
        else:
            try:
                result = search_on_spotify(search_value, search_type)
                return render_template('gettracks.html', data=me, result=result)
            except:
                raise Exception(f"Failed to find {search_type}: {search_value}!")

        

    return render_template('gettracks.html', data=me)

# Download page
@app.route('/download')
def download():
    # Init spotify API
    id = request.args.get('id')
    token_info = get_token()
    spotify = Spotify(auth=token_info["access_token"])
    # Make dirs if they dont exist
    if not os.path.exists(download_folder):
        os.mkdir(download_folder)
    if not os.path.exists(f'{download_folder}\covers'):
        os.mkdir(f'{download_folder}\covers')
    # Collect song infomation
    song = spotify.get_track_by_id(id)
    song_artist = song["artists"][0]["name"]
    song_name = song["name"]
    song_number = int(song["track_number"])
    album_name = song["album"]["name"]
    album_release_date = int(song["album"]["release_date"][:4])
    album_img_url = song["album"]["images"][0]["url"]
    album_img_download_url = f'{download_folder}\covers\{album_name}.jpeg'
    search_patern = f"{song_artist} - {song_name}"
    custom_filename = f"{download_folder}\\{song_artist} - {song_name} ({str(album_release_date)[:4]})" # Replace pytube generated file name
    # Save cover image
    if not os.path.exists(album_img_download_url):
        album_img = Image.open(requests.get(album_img_url, stream=True).raw)
        album_img.save(album_img_download_url)
    if not os.path.exists(custom_filename + ".mp3"):
        # Download song from youtube
        s = Search(search_patern)
        video = s.results[0]
        audio_mp4_only = video.streams.filter(only_audio=True, file_extension='mp4')[-1]
        audio_mp4_only.download(output_path=download_folder)
        pytube_mp4_title = audio_mp4_only.title
        print(f"Downloaded {pytube_mp4_title}.mp4")


        # Convert from mp4 to mp3
        for file in glob.glob(f"{download_folder}\\*.mp4"):
            escaped_pytube_mp4_title = addEscapeChar(pytube_mp4_title, ['(', ')', '[', ']'], '\\')
            escaped_pytube_mp4_title = removeChars(escaped_pytube_mp4_title, ['.', "'", ',', '"', '/', ':'])
            if re.search(escaped_pytube_mp4_title, file):
                # Swap titles
                os.rename(file, custom_filename + ".mp4")
                mp4_file = custom_filename + ".mp4"
            else:
                print(pytube_mp4_title, file)
        mp3_file = f'{mp4_file[:-3]}mp3'       
        ff = ffmpy.FFmpeg(
            executable='ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe',
            inputs={mp4_file: None},
            outputs={mp3_file: None}
        )
        ff.run()
        print(f" Converted {mp4_file} to {mp3_file}")
        os.remove(mp4_file)

        # Edit id3 metadata
        audiofile = eyed3.load(mp3_file)
        if (audiofile.tag == None):
            audiofile.initTag()
        audiofile.tag.title = f"{song_artist} - {song_name}"
        audiofile.tag.album = album_name
        audiofile.tag.artist = song_artist
        audiofile.tag.album_artist = song_artist
        audiofile.tag.track_num = song_number
        audiofile.tag.release_date = album_release_date
        audiofile.tag.images.set(3, open(album_img_download_url,'rb').read(), 'image/jpeg', description='Cover image')
        audiofile.tag.save()
    else:
        print(f"{custom_filename} already exists!")

    return render_template('download.html')

def addEscapeChar(str, substrs, char):
    for substr in substrs:
        if substr in [*str]:
            index = str.index(substr)
            str = str[:index] + char + str[index:]
    return str

def removeChars(str, chars):
    for char in chars:
        while char in [*str]:
            index = str.index(char)
            str = str[:index] + str[index + 1:]
    return str
def get_token():
    #get token from URL or refresh if expired
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        raise Exception("Couldn't get access token")
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify = create_spotify_oauth()
        token_info = spotify.refresh_access_token(token_info["access_token"])
    return token_info


def create_spotify_oauth():
    #Initialize spotify authorization
    return SpotifyOAuth(client_id=client_id,
        client_secret=client_secret,
        scope='playlist-read-private playlist-read-collaborative',
        redirect_uri=url_for('redirectPage', _external=True))

if __name__ == "__main__":
    app.run(debug=True)