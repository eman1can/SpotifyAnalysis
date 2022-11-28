# Spotify Analysis Flask Application

## Background

Relying on the [Spotipy Python library](https://spotipy.readthedocs.io/en/2.21.0/), our project requires some minimal setup to get live Spotify querying up and running. While not integral for the ML capabilities of the project, the integration does allow for testing on arbitrary data and enables our application to be much more applicable to the needs outlined in our proposal. For demonstration purposes, a `Demo` option has also been made available to run the model without the following setup instructions.

## Setup

Looking at [app.py](./app.py), we can see that a SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET are missing. These can be obtained by going to https://developer.spotify.com/dashboard/ and creating a new app. Also be sure to set LIVE_QUERY=True once done.

Once these are configured, the last step is to set a redirect URI on your Spotify app dashboard. A redirect has already been set in [app.py](./app.py), so all one needs to do is to copy and paste it into the `Redirect URI` field under the `Edit Settings` tab.