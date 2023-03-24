import pytube
# from pytube.cli import on_progress
from moviepy.video.io.VideoFileClip import VideoFileClip
from pathlib import Path

from datetime import timedelta
import time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter.messagebox import showinfo, showerror


def chek_if_num(text: str):
    if text in [".", ":"] or text.isdigit() or text == "":
        return True
    else:
        return False


class YoutubeDownloaderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.geometry("400x300")

        self.url_label = tk.Label(self, text="Enter YouTube URL:")

        self.url_entry = tk.Entry(self, width=50)

        self.download_button = tk.Button(
            self, text="Download Video", command=self.download_video)

        self.trim_button = tk.Button(
            self, text="Trim Video", command=self.trim_video)

        self.progress_bar_container = tk.Frame(self)

        self.output_path_label = tk.Label(self, text="Enter the path of the video that's going to be trimmed: ")

        self.output_path_entry = tk.Entry(self,
                width=50,
                validatecommand=(self.register(self.is_video_file_path_valid), '%S'))

        self.browse_button = tk.Button(
            self, text="Browse", command=self.browse_output_path)

        # create a container to hold labels
        self.labels_frame = tk.Frame(self)

        self.start_label = tk.Label(self.labels_frame, text="Start:")
        self.start_time_entry = tk.Entry(
            self.labels_frame, validate="key", validatecommand=(self.register(chek_if_num), '%S'))

        self.end_label = tk.Label(self.labels_frame, text="End:")
        self.end_time_entry = tk.Entry(self.labels_frame, validate="key", validatecommand=(
            self.register(chek_if_num), '%S'))

        self.start_label.grid(row=0, column=0)
        self.start_time_entry.grid(row=0, column=1)
        self.end_label.grid(row=1, column=0)
        self.end_time_entry.grid(row=1, column=1)

        self.url_label.pack()
        self.url_entry.pack()
        self.progress_bar_container.pack()
        self.download_button.pack()
        self.output_path_label.pack()
        self.output_path_entry.pack()
        self.browse_button.pack()

        self.labels_frame.pack()
        self.trim_button.pack()

        self.file_name = None
    
    def get_file_name_from_url(self, name: str) -> str:
        if "?" in name: 
            return ( name
                     .split("?")[1]
                     .replace("v=", ""))
        else:
            return name.split("/")[-1].replace("/", "")

    def download_video(self):
        url = self.url_entry.get()
        youtube = pytube.YouTube(
            url, on_progress_callback=lambda stream, chunk, bytes_remaining:
                self.update_progress_bar(
                    bytes_remaining, stream.filesize))
        
        file_name = self.get_file_name_from_url(url)

        # get the video stream with 4K reso\
        # =tion
        video_stream = youtube.streams.filter(res="2160p").first()

        # create folder videos if it doesn't exist
        Path("./videos").mkdir(parents=True, exist_ok=True)

        # store your file
        output_file_path = str(
            (Path("./videos") / f"{file_name}.mp4").resolve())

        # set the output path in the entry
        self.output_path_entry.delete(0, tk.END)
        self.output_path_entry.insert(0, output_file_path)

        # check if the video already exists
        if Path(output_file_path).exists():
            showinfo(message="Video already exists")
            return

        if video_stream is None:
            showerror(title="No 4K video stream available")
            return

        # initialize progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_bar_container, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack()
        self.progress_label = tk.Label(self.progress_bar_container, text="0%")
        self.progress_label.pack()
        self.start_time = time.time()

        self.file_name = file_name

        # download the video stream
        video_stream.download(filename=output_file_path)

    def is_video_file_path_valid(self):
        out_entry_name = self.output_path_entry.get()
        out_name_path = Path(out_entry_name)
        # check if the file exists
        if out_name_path.exists():
            self.trim_button.config(state="normal")

    def update_progress_bar(self, bytes_remaining, total_size):

        # calculate progress and show it
        bytes_downloaded = total_size - bytes_remaining
        percent_complete = bytes_downloaded / total_size * 100
        self.progress_bar["value"] = percent_complete
        self.progress_bar.update()

        # calculate remaining time and show it
        remaining_bytes = bytes_remaining
        bytes_per_second = (total_size - bytes_remaining) / \
            (time.time() - self.start_time)
        remaining_time = str(
            timedelta(seconds=int(remaining_bytes / bytes_per_second)))
        self.progress_label.config(
            text=f"{percent_complete:.1f}% - Remaining time: {remaining_time}")

        # destroy progress bar if download is complete
        if percent_complete == 100:
            self.progress_bar.destroy()
            self.progress_label.destroy()

    def trim_video(self):
        input_path_file = self.output_path_entry.get()
        start_time = self.start_time_entry.get()
        end_time = self.end_time_entry.get()
        file_name = (self.file_name if self.file_name is not None 
                     else Path(input_path_file).stem)

        # .subclip(startseconds, endseconds)
        trimmedvideo = VideoFileClip(
            input_path_file).subclip(start_time, end_time)
        trimmedvideo.write_videofile(
            f"./videos/{file_name}-trimmed.mp4", temp_audiofile="temp-audio.m4a")

    def browse_output_path(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".mp4",
                                                 filetypes=[("MP4 files", "*.mp4"), ("All files", "*.*")])
        self.output_path_entry.delete(0, tk.END)
        self.output_path_entry.insert(0, file_path)


if __name__ == "__main__":
    app = YoutubeDownloaderGUI()
    app.mainloop()
