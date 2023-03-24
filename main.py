import pytube
from pytube.cli import on_progress
from moviepy.video.io.VideoFileClip import VideoFileClip
from pathlib import Path

url = "https://www.youtube.com/watch?v=6GFPSmH_oSg"
youtube = pytube.YouTube(url, on_progress_callback=on_progress)
file_name = (url
             .split("?")[1]
             .replace("v=", ""))

# get the video stream with 4K resolution
video_stream = youtube.streams.filter(res="2160p").first()

# store your file
output_file_path = str((Path("./videos") / f"{file_name}.mp4").resolve())
print(f"{output_file_path=}")

if video_stream is None: 
    print("No 4K video stream available")
    exit(1)

print("Downloading video stream...")

# download the video stream
video_stream.download(filename=output_file_path)


input_path_file = output_file_path

print("Trimming video...")

# .subclip(startseconds, endseconds)
trimmedvideo = VideoFileClip(input_path_file).subclip(9, 19)
trimmedvideo.write_videofile(f"./videos/{file_name}-trimmed.mp4")
