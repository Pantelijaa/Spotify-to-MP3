import base64
import requests
import time
from urllib.parse import urlencode

class Spotify(object):

    """
    Use after initial authorization 
    """

    def __init__(self, auth=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.auth = auth

    def get_resource_header(self):
        auth = self.auth
        headers = {
            "Authorization": f"Bearer {auth}"
        }
        return headers

    def get_resource(self, lookup_id, resource_type='albums'):
        
        endpoint = f"https://api.spotify.com/v1/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()

    def get_album_by_id(self, _id):
        """
        get album by specific id
        """
        return self.get_resource(_id, resource_type='albums')
    
    def get_track_by_id(self, _id):
        """
        get track by specific id
        """
        return self.get_resource(_id, resource_type="tracks")

    def get_artist_by_id(self, _id):
        """
        get artist by specific id
        """
        return self.get_resource(_id, resource_type='artists')

    def get_playlists_by_user_id(self, _id):
        """
        get user's playlists by user id
        """
        modified_id = f"{_id}/playlists"
        data = self.get_resource(modified_id, resource_type='users')
        return data["items"]
    
    def get_playlist_tracks_by_id(self, _id):
        """
        get playlist tracks by playlist id
        """
        modified_id = f"{_id}/tracks"
        data = self.get_resource(modified_id, resource_type='playlists')
        return data["items"]

    def get_user_info(self):
        """
        get personal informations about logged user
        """
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/me/"
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()
    
    def base_search(self, query_params):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        lookup_url = f"{endpoint}?{query_params}"
        r = requests.get(lookup_url, headers=headers)
        if r.status_code not in range(200,299):
            return {}
        return r.json()

    def search(self, query=None,operator=None, operator_query=None, search_type=None):
        if query == None:
            raise Exception("A query is required")
        if search_type == None:
            raise Exception("Search type is required")
        if isinstance(query, dict):
            # dictionary into list
            query = " ".join([f"{k}:{v}" for k,v in query.items()])
        if operator != None and operator_query != None:
            if operator.lower() == "or" or operator.lower() == "not":
                operator = operator.upper()
                if isinstance(operator_query, str):
                    query = f"{query} {operator} {operator_query}"
        query_params = urlencode({"q": query, "type": search_type.lower()}, safe=',')
        return self.base_search(query_params)

class SpotifyOAuth(object):
    """
    Spotify Authorization 

    """
    token_url = "https://accounts.spotify.com/api/token"
    auth_url = "https://accounts.spotify.com/authorize"

    def __init__(self, client_id=None, client_secret=None, scope=None, redirect_uri=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        self.scope = scope
        self.redirect_uri = redirect_uri

    def get_client_credentials(self):
        """
        return base64 string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        if client_id == None or client_secret == None:
            raise Exception("client_id or _client secret not set")
        client_creds = f"{client_id}:{client_secret}"
        client_creds_64 = base64.b64encode(client_creds.encode()) 
        return client_creds_64.decode()

    def get_token_headers(self):
        client_creds_64 = self.get_client_credentials()
        return  {
            "Authorization": f"Basic {client_creds_64}"
        }

    def get_token_data(self): #prob obrisati
        return {
            "grant_type": "client_credentials"
        }

    def get_authorize_url(self):
        """
        Request authorization from the user to access data
        """
        data = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": self.scope
        }
        urlparams = urlencode(data)
        return "%s?%s" % (self.auth_url, urlparams)

    def get_access_token(self, code=None):
        """
        Request access and refresh token
        """
        token_url = self.token_url
        # data for Implicit Grant Flow
        token_data = self.get_token_data() #prob obrisati
        token_headers = self.get_token_headers()
        # data for Authorization Code Flow
        if code != None:
            token_data = {
                "redirect_uri": self.redirect_uri,
                "code": code,
                "grant_type": "authorization_code",
            }
        r = requests.post(token_url, data=token_data, headers=token_headers,)

        # check if request is valid (200-299)
        if r.status_code  not in range(200, 299):
            raise Exception("Couldn't authenticate client")

        token_info = r.json()
        token_info = self.add_custom_values_to_token_info(token_info)
        return token_info

    def add_custom_values_to_token_info(self, token_info):
        """
        Add expires at property to token_info
        """
        token_info["expires_at"] = int(time.time()) + token_info["expires_in"]
        return token_info