import base64

from flask import Flask, request, send_from_directory
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

app = Flask(__name__)

global_sessions = list()

def get_key(dict):
    message = u' '.join((dict['artist'], dict['title'])).encode('utf-8').strip()
    base64_bytes = base64.urlsafe_b64encode(message)
    return base64_bytes.decode('ascii')

import subprocess

def get_proc_name(AppId):
    cmd = f"get-StartApps | Where-Object {{$_.AppId -like '{AppId}'}} | Select Name | foreach {{ $_.Name }}"
    completed = subprocess.run(["powershell", "-Command", cmd], capture_output=True)

    if (completed.returncode != 0):
        return ''
    return completed.stdout.decode('ascii').replace('\r\n', '')

async def get_media_info():
    sessions = await MediaManager.request_async()

    for item in sessions.get_sessions():
        if item:
            obj = {}
            info = await item.try_get_media_properties_async()
            info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
            info1 = {}
            info1['title'] = info_dict['title']
            info1['artist'] = info_dict['artist']

            id = get_key(info1)
            info1['id'] = id
            obj['id'] = id

            info1['status'] = 'paused'

            if item.get_playback_info().playback_status == item.get_playback_info().playback_status.PLAYING:
                info1['status'] = 'playing'

            obj['info'] = info1
            obj['item'] = item

            index = next((index for (index, item) in enumerate(global_sessions) if item["id"] == obj['id']), -1)
            obj['info']['index'] = index
            obj['info']['source_app'] = get_proc_name(item.source_app_user_model_id)
            if (index == -1):
                obj['info']['index'] = 0
                global_sessions.insert(0, obj)
            else:
                global_sessions[index] = obj
    return global_sessions

@app.route("/")
def root():
    return send_from_directory('static', 'index.html')

@app.route("/sessions")
async def sessions():
    data = await get_media_info()
    return list(map(lambda x: x['info'], list(data)))

@app.route("/toggle")
async def toggle():
    id = request.args.get("id")
    action = request.args.get('action')
    data = await get_media_info()
    item = next((item for item in data if item["id"] == id), None)

    if id is None:
        return 400
    
    if item == None:
        return 404

    handle = item['item']

    if action:
        if action == 'prev':
            await handle.try_skip_previous_async()
        if action == 'next':
            await handle.try_skip_next_async()
    else:
        handle.try_toggle_play_pause_async()

    data = await get_media_info()
    return list(map(lambda x: x['info'], list(data)))
