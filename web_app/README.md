# Setup

Relying on the [Spotipy Python library](https://spotipy.readthedocs.io/en/2.21.0/), our project requires some minimal setup to get up and running. While not integral for the ML capabilities of the project, the integration does allow for live querying of Spotify data and make our application much more applicable to the needs outlined in our proposal.

Looking at [app.py](./app.py), we can see that a SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET are missing. These can be obtained by going to https://developer.spotify.com/dashboard/ and creating a new app.

Once these two are configured, the last step is to set a redirect URI. A redirect has already been set in [app.py](./app.py), so all one needs to do is to copy and paste it into the `Redirect URI` field under the `Edit Settings` tab.