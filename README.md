
<img src="https://i.imgur.com/qL25Z2J.png" alt="beat-logo" width="15%" align="right">

# Beat
**Beat** is a new free open source discord music bot for playing music from YouTube and Spotify. **Beat** is done on [Pycord](https://docs.pycord.dev/en/master/).

## 🔶 Bot invitation

If you want to invite the bot, [click here](https://discord.com/api/oauth2/authorize?client_id=883986382719189033&permissions=414526590016&scope=bot%20applications.commands).

## 📚 Commands

### /join
Joins to the voice channel.

### /play youtube-video-link | spotify-link | search-query
Bot joins to your voice channel and plays music from a link or search query.

### /lofi
Joins to the channel and plays lofi hip hop.

### /leave
Leaves the voice channel.

### /skip
Skips current song.

### /pause
Pauses current song.

### /resume
Resumes current song if it is paused.

### /queue
Shows current queue of songs.

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

## 🌌 Current Version
Current bot version is **1.2.3**.

## ⬇️ How to install the bot?

### 1. Install Python 3.9.x or 3.10.x
Go to the official python website (or just [click here](https://www.python.org/downloads/)) and download from there python 3.9.x or python 3.10.x

### 2. Install the dependencies
After installing python, open terminal and write this 7 commands:
````commandline
pip install -U py-cord --pre
pip install PyNaCl
pip install yt-dlp
pip install youtube-search-python
pip install pytube
pip install async-spotify
pip install ytmusicapi
````

### 3. Install the FFmpeg
To install the FFmpeg, [click here](https://github.com/BtbN/FFmpeg-Builds/releases) and choose the version you need. Then, unzip the archive in a folder convenient for you.

### 4. Get cookies.txt file
Before getting cookies.txt, make sure that you are logged in YouTube.

#### In Google Chrome:

Install this extension: https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid?hl=en

Go to YouTube.com, click on extensions in the right-up corner, Get cookies.txt, click on Export and save the file.

#### In Firefox:

Install this extension: https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/

Go to YouTube.com, click on cookies in the right-up corner, click on "Current Site", and save the file

#### In other browsers:

In other browsers, just google "How to get cookie.txt in your_browser"

### 5. Create spotify application.

Follow [this link](https://developer.spotify.com/dashboard/applications) and create here an application.
After that, copy your client id and your client secret.

### 6. Change the config.py
First, you need to download [the latest release](https://github.com/Knedme/Beat/releases) of bot.

Then, open config.py in any text editor and write there your token from discord developers portal, paths to files, spotify app client id and client secret like that:

![config.py](https://i.imgur.com/gPnc0jy.png)

### 7. Run the bot
Finally, open terminal in the folder where your bot is located and write:
```commandline
python main.py
```

Congratulations, you have successfully installed the bot and launched it.

## 🆘 Support
If you find a bug, or you have a question please write here: Knedme#3143 or Knedme@yandex.ru
