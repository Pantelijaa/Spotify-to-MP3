# "C:\Python310\lib\ssl.py", line 579 modified
from flask import Flask, request, url_for, session, redirect, render_template
from EjPiAj import *
import time
from pytube import  Search
import glob
import re
import ffmpy
import os

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

@app.route('/download')
def download():
    artist = request.args.get('artist')
    song = request.args.get('song')
    search_patern = f"{artist} - {song}"
    try:
        s = Search(search_patern)
        video = s.results[0]
        audio_mp4_only = video.streams.filter(only_audio=True, file_extension='mp4')[-1]
        audio_mp4_only.download(output_path=download_folder) #dodati download path
    except:
        raise Exception(f"Failed to find any result for {search_patern}!")

    # convert from mp4 to mp3
    # ako vec ima mp3 -> error
    try:
        for file in glob.glob(f"{download_folder}\\*.mp4"):
            if re.search(artist.lower() , file.lower()) and (song.lower() , file.lower()):
                mp4_file = file
        mp3_file = f'{mp4_file[:-3]}mp3'       
        ff = ffmpy.FFmpeg(
            executable='ffmpeg-master-latest-win64-gpl\\bin\\ffmpeg.exe',
            inputs={mp4_file: None},
            outputs={mp3_file: None}
        )
        ff.run()
        os.remove(mp4_file)
    except:
        raise Exception(f'Error while converting to .mp3 file extension')

    return render_template('download.html')

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