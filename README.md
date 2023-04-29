
<img src="https://raw.githubusercontent.com/Knedme/Beat/master/logo/round1x.png" alt="beat-logo" width="15%" align="right">

# Beat
**Beat** is a free open source discord music bot for playing music from YouTube and Spotify. **Beat** is done on [Nextcord](https://docs.nextcord.dev/en/stable/).

Bot structure from: https://github.com/BaggerFast/NextcordTemplate

## 🔶 Bot invitation
If you want to invite the bot, use [this](https://discord.com/api/oauth2/authorize?client_id=883986382719189033&permissions=414526590016&scope=bot%20applications.commands) or [this link](https://discord.com/api/oauth2/authorize?client_id=1028606605593432134&permissions=414526590016&scope=bot%20applications.commands).

## 🌌 Current Version
Current bot version is **1.3.7**.

## 📚 Commands

### /join
The bot joins to your voice channel.

### /play youtube-video-link | spotify-link | search-query
The bot joins to your voice channel and plays music from a link or search query.

### /lofi
The bot joins to your channel and plays lofi.

### /leave
Leave the voice channel.

### /skip
Skips current song.

### /pause
Pauses current song.

### /resume
Resumes current song if it is paused.

### /queue
Shows current queue.

### /now-playing
Shows what song is playing now.

### /loop
Enables/Disables Queue/Track loop.

### /shuffle
Shuffles next songs in the queue.

### /support
Shows support contact.

### /commands
Shows a list of commands.

### /info 
Shows information about the bot.

## ⬇️ Getting started

### 1. Install Python 3.11.2

### 2. Clone this repo
Install Git and run this command in the terminal:
```commandline
git clone https://github.com/Knedme/Beat.git
```

### 3. Install the dependencies
Run this command in the terminal in the cloned Beat folder:
````commandline
pip install -r requirements.txt
````

### 4. Install the FFmpeg on your OS

### 5. Get cookies.txt file (not necessary, but recommended)
To do this, just google something like `How to get cookies.txt file in <your-browser-name>`

### 6. Create a Spotify application

Follow [this link](https://developer.spotify.com/dashboard/applications) and create there an application.

### 7. Set the environment variables
Set the environment variables `TOKEN`, `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`.

### 8. Change the bot config
Open `<beat-folder>/bot/misc/config.py` file in any text editor and define there FFmpeg executable file path and cookies.txt file path (if you have one).

### 9. Run the bot
Open terminal in the cloned Beat folder and run the bot:
```commandline
python run.py
```

## 📦 Docker

You can also run **Beat** using Docker:
```commandline
sudo docker build -t beat:version /your-beat-folder
sudo docker run -d -v /path-to-changed-config:/beat/bot/misc/config.py \
-v /path-to-cookies:/path-to-cookies-in-config -e TOKEN=YOUR_TOKEN \
-e SPOTIFY_CLIENT_ID=YOUR_CLIENT_ID \
-e SPOTIFY_CLIENT_SECRET=YOUR_CLIENT_SECRET beat:version
```

## 🆘 Support
If you find a bug, or you have a question please write here: `supknedme@yandex.com`
