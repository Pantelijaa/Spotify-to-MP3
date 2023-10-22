# Python310\Lib\ssl.py, line 579 modified
from flask import Flask, request, url_for, session, redirect, render_template, abort
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
from dotenv import load_dotenv

def get_download_path():
    """
    Returns the default downloads path for linux or windows
    """
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')

load_dotenv()
client_id = os.getenv('CLIENT_ID') # Spotify API Client ID
client_secret = os.getenv('CLIENT_SECRET') # Spotify API Client Secret
download_folder = get_download_path() # Path to download folder

app = Flask(__name__)

app.secret_key = os.getenv('SECRET_KEY') # random
app.config['SESSION_COOKIE_NAME'] = 'Moj Kolacic'
TOKEN_INFO = "token_info"

# Home page
@app.route('/')
def home():
    """
    Login to personal spotify
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
    Redirect to respond page with code
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
    if request.method == 'POST':
        search_value = request.form['search-value']
        search_type = request.form['search-type']
        try:
            return render_template('gettracks.html', data=me, result=search_on_spotify(search_value, search_type, spotify))    
        except:
            abort(500, description=f"Failed to find {search_type} \"{search_value}\"")
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
    # Collect song information
    song = spotify.get_track_by_id(id)
    song_artist = song["artists"][0]["name"]
    song_name = song["name"]
    song_number = int(song["track_number"])
    album_name = song["album"]["name"]
    escaped_album_name = removeChars(album_name, ['.', "'", ',', '"', '/', ':', '*', '$', '?'])
    album_release_date = int(song["album"]["release_date"][:4])
    album_img_url = song["album"]["images"][0]["url"]
    album_img_download_url = f'{download_folder}\covers\{escaped_album_name}.jpeg'
    search_patern = f"{song_artist} - {song_name}"
    modified_song_name = removeChars(song_name, ['*', '"' ,'?'])
    custom_filename = f"{download_folder}\\{song_artist} - {modified_song_name} ({str(album_release_date)})" # Replace pytube generated file name
    # Save cover image
    if not os.path.exists(album_img_download_url):
        album_img = Image.open(requests.get(album_img_url, stream=True).raw)
        album_img.save(album_img_download_url)
    if os.path.exists(custom_filename + ".mp3"):
        abort(500, description=f"{custom_filename} already exists")
    else:
        # Download song from youtube
        s = Search(search_patern)
        video = s.results[0]
        video.use_oauth = True
        audio_mp4_only = video.streams.filter(only_audio=True, file_extension='mp4')[-1]
        audio_mp4_only.download(output_path=download_folder)
        pytube_mp4_title = audio_mp4_only.title
        escaped_pytube_mp4_title = removeChars(pytube_mp4_title, ['.', "'", ',', '"', '/', ':', '*', '$', '?',])
        escaped_pytube_mp4_title = addEscapeChar(escaped_pytube_mp4_title, ['(', ')', '[', ']'], '\\')
        print(f"Downloaded {pytube_mp4_title}.mp4")
        print(f"escaped title: {escaped_pytube_mp4_title}")

        # Convert from mp4 to mp3
        for file in glob.glob(f"{download_folder}\\*.mp4"):
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
        audiofile.tag.images.set(3, open(album_img_download_url,'rb').read(), 'image/jpeg', description='Cover image') # ne radi
        audiofile.tag.save()

    return render_template('download.html')

@app.route('/force_logout')
def force_logout():
    session[TOKEN_INFO] = None
    return '', 204

@app.errorhandler(500)
def internal_error(e):
    return render_template('error.html', error=e), 500

def search_playlist(name, spotify):
    me = spotify.get_user_info()
    playlists = spotify.get_playlists_by_user_id(me["id"])
    for elem in playlists:
        for val in elem.values():
            if val == name:
                return elem['id']
    
def search_on_spotify(name, type, spotify):
    if type == 'any':
        type = 'track,album,artist'
    result = spotify.search(query=name, search_type=type)
    if 'album' in type:
        albums = list()
        for item in result['albums']['items']:
            id = item['id']
            get_album = spotify.get_album_by_id(id)
            for elem in get_album['tracks']['items']:
                elem['duration'] = convert_from_miliseconds_to_minutes(elem['duration_ms'])
            albums.append(get_album)
        result['albums'] =  albums
    elif type == 'playlist':
        playlist_id = search_playlist(name, spotify)
        result = {'playlist': spotify.get_playlist_tracks_by_id(playlist_id)}
    return result

def addEscapeChar(str, substrs, char):
    s = str
    counter = 0
    for i, ltr in enumerate(s):
        for substr in substrs:
            if ltr == substr:
                i += counter
                s = s[:i] + char + s[i:]
                counter +=1
    return s

def removeChars(str, chars):
    for char in chars:
        while char in [*str]:
            index = str.index(char)
            str = str[:index] + str[index + 1:]
    return str

def convert_from_miliseconds_to_minutes(ms):
    secs= int(ms/1000)
    minutes=0
    while secs >= 60:
        secs -= 60
        minutes +=1
    if secs < 10:
        secs = '0' + str(secs)
    return f'{minutes}:{secs}'

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