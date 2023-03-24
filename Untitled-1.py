# %%
from pathlib import Path
import re
import pandas as pd
import pytube
from pytube.cli import on_progress
from pytube.streams import Stream
import tqdm
from moviepy.video.io.VideoFileClip import VideoFileClip
from multiprocessing.dummy import Pool as ThreadPool
from pytube.monostate import Monostate

# %%
folder_name = "./videos/"

# %%
def get_id_from_youtube_url(url: str) -> pd.Series:
    pattern = re.compile(r"(?:\/|%3D|v=|vi=)([0-9A-Za-z_-]{11})(?:[%#?&]|$)")
    match = pattern.search(url)
    return match.group(1) if match else None

def download_video(video_stream: Stream, file_name: str) -> bool:
    output_file_path = str(
        (Path(folder_name) / f"{file_name}.mp4").resolve())
    try:
        video_stream.download(filename=output_file_path)
    except Exception as e:
        print(e)
        return False
    return True


# %%
df = pd.read_excel('./Book1.xlsx')
df = df.drop(['Unnamed: 0'], axis=1, errors="ignore")
df.head()

# %%
link_column = 'link'
time_stamp_column = 'time stamp'
# drop if the linkcolumn or time_stamp_column is empty
df = df.dropna(subset=[link_column, time_stamp_column])
# extract time stamp into start and end columns
df[['start', 'end']] = df[time_stamp_column].str.split(',', expand=True)
# extract the video id from the link
df['video_id'] = df[link_column].apply(get_id_from_youtube_url)
df.head()

# %%
def is_match(start_time_1: str, end_time_1: str, start_time_2: str, end_time_2: str) -> bool:
    # Convert start and end times to seconds
    start_1_sec = to_seconds(start_time_1)
    end_1_sec = to_seconds(end_time_1)
    start_2_sec = to_seconds(start_time_2)
    end_2_sec = to_seconds(end_time_2)

    # Check if the time windows overlap
    return start_1_sec <= end_2_sec and end_1_sec >= start_2_sec

def to_seconds(time: str) -> float:
    parts = time.split(':')
    times = [3600, 60, 1]
    parts = ['0'] * (3 - len(parts)) + parts # add zeros to the beginning of the list if the time is not in the format hh:mm:ss
    return sum([int(part) * time for part, time in zip(parts, times)])

# %%
from collections import defaultdict

new_df = [] 

video_id = str
time_window = tuple[str, str]
counting_dict: dict[video_id, list[time_window]] = defaultdict(list)
vid_id_counting_dict: dict[video_id, int] = defaultdict(int)

def is_time_window_already_present(time_windows_list: list[time_window], start_time: str, end_time: str) -> bool:
    for start_1, end_1 in time_windows_list:
        if is_match(start_1, end_1, start_time, end_time): # If already present 
            return False
    return True

for index, row in df.iterrows():
    video_id = row['video_id']
    start = row['start']
    end = row['end']

    vid_id_counting_dict[video_id] += 1

    if vid_id_counting_dict[video_id] > 3: 
        print("Already has more than three videoos with the same id")
        continue

    if video_id in counting_dict:
        if not is_time_window_already_present(counting_dict[video_id], start, end):
            counting_dict[video_id].append((start, end))

# %%
test_df = df.head(3)

# %%
total_size_files_bytes = 0
no_4k_stream = []
yt_streams = []
stream_progress_bar = tqdm.tqdm(total=len(test_df))

for index, row in test_df.iterrows():
    url = row[link_column]
    youtube = pytube.YouTube(url, on_progress_callback=on_progress).streams.filter(res="2160p").first()
    if youtube is None:
        print("No 4K video stream available")
        no_4k_stream.append(url)
        continue
    total_size_files_bytes += youtube.filesize
    yt_streams.append(youtube)
    stream_progress_bar.update(1)

stream_progress_bar.close() 

# %%
# create folder videos if it doesn't exist
Path(folder_name).mkdir(parents=True, exist_ok=True)

# %%
pbar = tqdm.tqdm(total = len(yt_streams))
for stream, vid_id in zip(yt_streams, test_df['video_id']):
    results = download_video(stream, vid_id)
    pbar.update(1)
del pbar

# %%
def trim_vid(input_file: Path, start_time: str, end_time: str):
    input_file_path = str(input_file.resolve())
    file_name = input_file.stem
    # .subclip(startseconds, endseconds)
    trimmedvideo = VideoFileClip(
        input_file_path).subclip(start_time, end_time)
    folder_path = Path(folder_name)
    new_file_name = Path(f"{file_name}-trimmed.mp4")
    out_file_path = folder_path / new_file_name
    trimmedvideo.write_videofile(
        out_file_path, temp_audiofile="temp-audio.m4a")

# %%
# go to the videos folder if the video has -trimmed in the name skip it else trim the video 
skip_vids = set()
trim_vid_args: list[tuple[Path, str, str]] = []
for file in Path(folder_name).iterdir():
    if '-trimmed' in file.name or file.name in skip_vids:
        skip_vids.add(file.name)
        continue
    video_id = file.stem
    start_time = test_df[test_df['video_id'] == video_id]['start'].values[0]
    end_time = test_df[test_df['video_id'] == video_id]['end'].values[0]
    trim_vid_args.append((file, start_time, end_time))

# %%
pbar = tqdm.tqdm(total=len(trim_vid_args))
# use multi threading to trim the videos
for input_file, start_time, end_time in trim_vid_args:
    trim_vid(input_file, start_time, end_time)
    pbar.update(1)


