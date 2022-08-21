# Config file

TOKEN = 'bot-token'  # write here your bot token
BOT_COLOR = 0x515596  # color of embeds
FFMPEG_PATH = r'C:\ffmpeg\ffmpeg.exe'  # write here your ffmpeg path
COOKIES_FILE_PATH = r'.\cookies.txt'  # write here your cookies file path
SPOTIFY_CLIENT_ID = 'client-id'  # write here your spotify client id
SPOTIFY_CLIENT_SECRET = 'client-secret'  # write here your spotify client secret

FFMPEG_OPTIONS = {  # ffmpeg options
	'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
	'options': '-vn'
}
