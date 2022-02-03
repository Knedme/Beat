# Config file

token = "bot-token"  # write here your bot token

ffmpeg = "C:/ffmpeg/ffmpeg.exe"  # write here your ffmpeg path

cookies = "D:/BeatCookies/cookies.txt"  # write here your cookies file path

spotify_client_id = "client-id"  # write here your spotify client id

spotify_client_secret = "client-secret"  # write here your spotify client secret

prefix = "+"  # command prefix

ffmpeg_options = {  # ffmpeg options
	"before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
	"options": "-vn"
}
