import youtube_dl
import subprocess
import os
import sys
import requests
from raven import Client

yt_url = sys.argv[1]
api_url = sys.argv[2]
client = Client('https://REDACTED:REDACTED@sentry.io/115546')


# download metadata
ydl = youtube_dl.YoutubeDL({'restrictfilenames': 'true', 'noplaylist': True})
r = None
url = yt_url
with ydl:
    r = ydl.extract_info(url, download=False)  # don't download, much faster

options = {
    'noplaylist' : True,
    'format': 'bestaudio/best', # choice of quality
    'extractaudio' : True,      # only keep the audio
    'audioformat' : "mp3",      # convert to mp3
    'outtmpl': r['title']+'.mp3',
    'verbose': True,
    'prefer_ffmpeg': True,
    'postprocessor_args': '-filter:a "atempo=2.0"'
    }
try:
	with youtube_dl.YoutubeDL(options) as ydl:
	    ydl.download([yt_url])
except:
	client.captureException()

# Call subprocess for S3 upload
#print('s4cmd put --API-ACL=public-read "{filename}" s3://grabthataudio/{filename}'.format(filename=str(r['title'])+'.mp3'))
s3uplaod = subprocess.call(['s4cmd put --API-ACL=public-read --config=".s3cfg" --API-StorageClass=STANDARD_IA --API-ContentType="audio/mpeg" "{filename}" "s3://grabthataudio/{filename}"'.format(filename=str(r['title'])+'.mp3')], shell=True)

#print('Return code: ' + str(s3uplaod))

if s3uplaod != 0:
	client.captureMessage('Issue uploading file to S3. Check to see if {title} already exists'.format(title=r['title']+'.mp3'))

data = {'filename': r['title']+'.mp3'}
api = requests.post(url=api_url, data=data)
#print(api.text)
