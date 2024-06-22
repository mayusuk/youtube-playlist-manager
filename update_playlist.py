# -*- coding: utf-8 -*-

# Sample Python code for youtube.playlistItems.insert
# See instructions for running these code samples locally:
# https://developers.google.com/explorer-help/code-samples#python

import os

import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import time

scopes = ["https://www.googleapis.com/auth/youtube.force-ssl",
          "https://www.googleapis.com/auth/youtubepartner",
          "https://www.googleapis.com/auth/youtube",
          "https://www.googleapis.com/auth/youtube.readonly"]

def main():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "mayur_khandave_project-client.json.json"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    credentials = flow.run_local_server(port=0)
    
    
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials, num_retries=3)
    
    added = set()

    video_added_file_exists = os.path.isfile("video_ids_already_added.txt")
    if video_added_file_exists:
      video_ids_already_added_file = open("video_ids_already_added.txt", "r")
      for video_id in video_ids_already_added_file:
        added.add(video_id.strip("\n"))

    not_found_song = open("not_working_song_id.txt", "w+")
    video_ids_file = open("video_ids.txt", "r")

    for video_id in video_ids_file:
      video_id = video_id.strip("\n")

      if video_id in added:
         print("Video {} already added".format(video_id))
         continue
      
      if not check_song_present(video_id, youtube):
         not_found_song.write(video_id)
         not_found_song.write("\n")
         continue
      
      add_to_playlist("PLD7Qg9cVYoszGtrKTm9FoTyfvLNEJ7IjF", video_id, youtube)
      time.sleep(1)


def add_to_playlist(playlistId, videoId, youtube):
    print("Adding Video {}".format(videoId))
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
          "snippet": {
            "playlistId": playlistId,
            "resourceId": {
              "kind": "youtube#video",
              "videoId": videoId
            }
          }
        }
    )
    response = request.execute()

def check_song_present(id, youtube):
    request = youtube.videos().list(
        part="snippet",
        id=id
    )

    response = request.execute()
    
    if response.get("pageInfo").get("totalResults") > 0:
      print("Video {} present".format(id))
      return True
    
    print("Video {} not present".format(id))
    return False

if __name__ == "__main__":
    main()