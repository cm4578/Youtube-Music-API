from fastapi import FastAPI, HTTPException
from pytube import YouTube
from ytmusicapi import YTMusic
import random
from collections import deque
import uvicorn
import httpx
from cachetools import TTLCache
from urllib.parse import urlparse
import yt_dlp
import json

app = FastAPI()
ytMusic = YTMusic()
video_cache = TTLCache(maxsize=100, ttl=3600)


youtube_music_headers = {
  'Content-Type': 'application/json',
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36 Edg/105.0.1343.42',
  'Accept-Language': 'de,de-DE;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
  'X-Goog-Api-Key': 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
  'prettyPrint': 'false',
  'X-Goog-FieldMask': 'streamingData.adaptiveFormats'
}

youtube_music_body = {
    "context": {
        "client": {
            "clientName": "ANDROID_MUSIC",
            "clientVersion": "5.28.1",
            "platform": "MOBILE",
            "hl": "en",
            "visitorData": "CgtEUlRINDFjdm1YayjX1pSaBg%3D%3D",
            "androidSdkVersion": 30,
            "userAgent": "com.google.android.apps.youtube.music/5.28.1 (Linux; U; Android 11) gzip",
        }
    },
    "videoId": "eOtATMfvfg8",
}


@app.get("/search/{filter}/{query}")
def explore_music(filter: str,query: str):
    search_results = ytMusic.search(query=query, filter=filter)
    return search_results

@app.get("/searchKeyWords/{query}")
def explore_music(query: str):
    search_results = ytMusic.get_search_suggestions(query=query)
    return search_results

@app.get("/getHome")
def get_home():        
    results = ytMusic.get_home()    
    filtered_contents = [item for item in results if "title" in item and "video" not in item["title"].lower()]
    return filtered_contents

@app.get("/getArtist/{id}")
def get_artist(id: str):
    data_list = ytMusic.get_artist(channelId=id)    
    return data_list

@app.get("/getAlbum/{browseId}")
def get_album(browseId: str):        
    data_list = ytMusic.get_album(browseId=browseId)
    return data_list



@app.get("/getWatchList/{videoId}")
def get_watch_play_list(videoId: str):    
    data_list = ytMusic.get_watch_playlist(videoId=videoId)
    data_list['tracks'] = data_list['tracks'][:15]
    return data_list

@app.get("/getAlbumBrowseId/{audioPlaylistId}")
def get_album(audioPlaylistId: str):        
    browserId = ytMusic.get_album_browse_id(audioPlaylistId=audioPlaylistId)    
    return browserId

@app.get("/getPlaylist/{audioPlaylistId}")
def get_play_list(audioPlaylistId: str):    
    data_list = ytMusic.get_playlist(playlistId=audioPlaylistId)    
    return data_list

@app.get("/getSongRelated/{browseId}")
def get_song_related(browseId: str):    
    data_list = ytMusic.get_song_related(browseId=browseId)
    return data_list

@app.get("/getAudioUrl/{video_id}")
async def get_audio_url_handler(video_id: str):
    try:
        youtube_url = f"https://music.youtube.com/youtubei/v1/player"
        quality_order = {"high": 3, "medium": 2, "low": 1}
        youtube_music_body['videoId'] = video_id

        # 嘗試從緩存中獲取視頻信息
        if video_id in video_cache:
            return {"audioUrl": video_cache[video_id]}

        async with httpx.AsyncClient() as client:
            response = await client.post(youtube_url, headers=youtube_music_headers, data=json.dumps(youtube_music_body))
            response.raise_for_status()

            adaptive_formats = json.loads(response.text)["streamingData"]["adaptiveFormats"]

            filtered_formats = [fmt for fmt in adaptive_formats if "audio" in fmt.get("mimeType", "").lower() and "audio" in fmt.get("url", "").lower()]
            if filtered_formats:
                sorted_formats = sorted(filtered_formats, key=lambda x: (quality_order.get(x.get("quality"), 0), x.get("bitrate", 0)), reverse=True)
                audio_url = sorted_formats[0]["url"]
                # 將視頻信息存入緩存
                video_cache[video_id] = audio_url
                return {"audioUrl": audio_url}
            else:
                raise HTTPException(status_code=404, detail="No audio formats found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting audio URL: {str(e)}")

    
if __name__ == "__main__":
    # local_ip = socket.gethostbyname(socket.gethostname())
    uvicorn.run("main:app", host="0.0.0.0", port=8010)    
