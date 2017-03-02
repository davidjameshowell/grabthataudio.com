from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, g
from hyper_sh import Client
import urllib
import youtube_dl
import boto3
import json
import base64
from raven.contrib.flask import Sentry


app = Flask(__name__)
app.secret_key = 'APP_SECRET'
sentry = Sentry(app, dsn='https://REPLACEME:REPLACEME@sentry.io/115538')

@app.route('/')
def index():
	return render_template('submit.html')

@app.route('/process', methods=['POST'])
def ytdl():
	error = False
	yurl = request.form['youtube_url']
	api_url = "http://requestb.in/19ot1p21"
	ydl_opts = {'noplaylist': True}
	ydl = youtube_dl.YoutubeDL(ydl_opts)
	r = None
	url = yurl
	try:
		r = ydl.extract_info(url, download=False)  # don't download, much faster
		title = r['title']
		uploader = r['uploader']
		thumbnail = r['thumbnails'][0]['url']
		filename = r['title'] + ".mp3"
		display_data = {'title': title, 'uploader': uploader, 'thumbnail': thumbnail, 'poll': base64.b64encode(filename.encode('utf-8'))}
		s3 = boto3.client('s3')
		print(r['title'] + ".mp3")
		try:
			s3.head_object(Bucket='grabthataudio', Key=filename)
			return render_template('processing.html', display_data=display_data)
		except:
			container_id = create_container(api_url, yurl)
			print('Container logs ' + poll_logs(container_id))
			return render_template('processing.html', display_data=display_data)
	except youtube_dl.utils.DownloadError, e:
		#print('We encountered an error.')
		error_end = str(e).find('said: ')
		#print(error_end)
		yt_error = str(e)[error_end + 6:]
		#print(yt_error)
		sentry.captureMessage('Error in YT parse. See error: ' + yt_error)
		flash('Uh oh! We encounted the following error: {error}'.format(error=yt_error))
        return redirect(url_for('index'))

@app.route('/poll/<filename>')
def poll_s3(filename):
	decoded_filename = base64.b64decode(filename)
	double_decode = urllib.unquote(decoded_filename).decode("utf8")
	s3 = boto3.client('s3')
	try:
   		s3.head_object(Bucket='grabthataudio', Key=double_decode)
   		return jsonify(ready=True)
	except:
		return jsonify(ready=False)
	return jsonify(ready=False)

@app.route('/contlogs/<guid>')
def poll_logs(guid):
	import re
	c = Client("./hyper_config.json")
	logs = c.logs(guid)
	split_string = re.split('\n|\r', logs)
	concat = ""
	for item in split_string:
		print(item)
		concat += item + "<br />"
	return "<div>" + concat + "</div>";

def create_container(api, yt_url):
	c = Client("./hyper_config.json")
	# working_dir="/tmp"
	container = c.create_container(labels={"sh_hyper_instancetype": "s3", 'sh_hyper_noauto_volume': 'true'}, image="1dcb5ad1", command='python3 process_file.py "{yt_url}" "{api_url}"'.format(yt_url=yt_url, api_url=api))
	response = c.start(container=container.get("Id"))
	return container.get("Id")

@app.route('/docker-image-pull', methods=['GET'])
def pull_image_hyper():
	auth = {'username':'replaceme', 'password':'replaceme'}
	c = Client("./hyper_config.json")
	line_concat = ""
	for line in c.pull(repository='REPO', stream=True, auth_config=auth):
		line_concat += json.dumps(json.loads(line))
	return line_concat

@app.errorhandler(500)
def internal_server_error(error):
    return render_template('500.html',
        event_id=g.sentry_event_id,
        public_dsn=sentry.client.get_public_dsn('https')
    )
