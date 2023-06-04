# import win32api
# from win32con import VK_MEDIA_PLAY_PAUSE, KEYEVENTF_EXTENDEDKEY
import jsonpickle
import asyncio
import uuid

from flask import Flask, request, send_from_directory
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager

app = Flask(__name__)

mapping = {}

def get_key(index):
    return str(index)

async def get_media_info():
    sessions = await MediaManager.request_async()
    x = list()
    index = 0
    for item in sessions.get_sessions():
        if item:
            info = await item.try_get_media_properties_async()
            info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}

            new_dict = {}
            new_dict['title'] = info_dict['title']
            new_dict['artist'] = info_dict['artist']
            new_dict['index'] = index
            new_dict['status'] = 'paused'

            if get_key(index) not in mapping:
                id = str(uuid.uuid4())
                mapping[get_key(index)] = id
            new_dict['id'] = mapping.get(get_key(index))
            index = index + 1

            if item.get_playback_info().playback_status == item.get_playback_info().playback_status.PLAYING:
                new_dict['status'] = 'playing'

            x.append(new_dict)
    return x

@app.route("/")
def root():
    return send_from_directory('static', 'index.html')

@app.route("/sessions")
def hello_world():
    current_media_info = asyncio.run(get_media_info())
    return jsonpickle.decode(jsonpickle.encode(current_media_info))

@app.route("/toggle")
async def toggle():
    args = request.args
    id = args.get("id")
    sessions = await MediaManager.request_async()
    x = list()

    if id is None:
        return 404
    
    index = 0
    
    for item in sessions.get_sessions():
        if item:
            info = await item.try_get_media_properties_async()
            info_dict = {song_attr: info.__getattribute__(song_attr) for song_attr in dir(info) if song_attr[0] != '_'}
            idd = mapping.get(get_key(index))
            new_dict = {}
            new_dict['title'] = info_dict['title']
            new_dict['artist'] = info_dict['artist']
            new_dict['id'] = idd
            new_dict['index'] = index

            is_playing = item.get_playback_info().playback_status == item.get_playback_info().playback_status.PLAYING

            if (is_playing):
                new_dict['status'] = 'playing'
            else:
                new_dict['status'] = 'paused'

            if id == idd:
                if is_playing:
                    new_dict['status'] = 'paused'
                    await item.try_pause_async()
                else:
                    new_dict['status'] = 'playing'
                    await item.try_play_async()

            index = index + 1
            x.append(new_dict)

    return jsonpickle.decode(jsonpickle.encode(x))
