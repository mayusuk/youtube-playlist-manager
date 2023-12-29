

f = open("_chat.txt")

count = 0

not_songs = []
songs = []
for line in f:
    index = line.find("https")
    if index >= 0:
        song = line[index:].strip("\n")
        # print(song)
        count += 1
        songs.append(song)
    else:
        not_songs.append(line)
    
# print(count,len(not_songs))
        
# print(songs)

video_ids = []
song_without_video_ids = []
for song in songs:
    index = song.find("?v=")
    if index >= 0:
        video_id = song[index+3:].split("&")[0]
        video_ids.append(video_id)
    elif song.find("youtu.be") >= 0:
        video_ids.append(song.split("https://youtu.be/")[1])
    else:
        song_without_video_ids.append(song)
# print(video_ids,len(video_ids))
print(song_without_video_ids)


video_ids_file = open("video_ids.txt", "w")

for id in video_ids:
    video_ids_file.write(id)
    video_ids_file.write("\n")

