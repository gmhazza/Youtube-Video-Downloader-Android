import os
import threading
import yt_dlp
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock

class DownloaderUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=15, spacing=12, **kwargs)

        self.add_widget(Label(text="YouTube Downloader", size_hint=(1, None), height=32))

        # URL input
        self.add_widget(Label(text="YouTube URL", size_hint=(1, None), height=24))
        self.url_input = TextInput(hint_text="https://youtube.com/...", multiline=False)
        self.add_widget(self.url_input)

        # Mode select
        self.add_widget(Label(text="Mode", size_hint=(1, None), height=24))
        self.mode_spinner = Spinner(text="Video", values=("Video", "Audio"), size_hint=(1, None), height=40)
        self.add_widget(self.mode_spinner)

        # Quality select
        self.add_widget(Label(text="Quality (video: best/720/1080 | audio: 128/192/320)", size_hint=(1, None), height=24))
        self.quality_input = TextInput(hint_text="Leave empty for best", multiline=False)
        self.add_widget(self.quality_input)

        # Path selector
        self.add_widget(Label(text="Save to", size_hint=(1, None), height=24))
        default_dir = App.get_running_app().user_data_dir
        # Common Android dirs (app must have storage permission to access these)
        self.path_spinner = Spinner(
            text="App Storage",
            values=("App Storage", "Downloads", "Documents"),
            size_hint=(1, None), height=40
        )
        self.add_widget(self.path_spinner)

        # Download button
        self.download_btn = Button(text="Download", size_hint=(1, None), height=48)
        self.download_btn.bind(on_press=self.start_download_thread)
        self.add_widget(self.download_btn)

        # Progress bar
        self.progress_bar = ProgressBar(max=100, value=0, size_hint=(1, None), height=26)
        self.add_widget(self.progress_bar)

        # Status label
        self.status = Label(text="Ready", size_hint=(1, None), height=28)
        self.add_widget(self.status)

        self.base_paths = {
            "App Storage": default_dir,
            "Downloads": "/storage/emulated/0/Download",
            "Documents": "/storage/emulated/0/Documents"
        }

    def _ui_update(self, text=None, pct=None):
        if text is not None:
            self.status.text = text
        if pct is not None:
            try:
                self.progress_bar.value = float(pct)
            except:
                pass

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            p = d.get('_percent_str', '0%').replace('%', '').strip()
            sp = d.get('_speed_str', '')
            eta = d.get('_eta_str', '')
            Clock.schedule_once(lambda dt: self._ui_update(
                text=f"Downloading: {p}% | {sp} | ETA {eta}", pct=p))
        elif d['status'] == 'finished':
            Clock.schedule_once(lambda dt: self._ui_update(text="Download complete. Merging...", pct=100))

    def start_download_thread(self, *_):
        url = self.url_input.text.strip()
        mode = self.mode_spinner.text
        q = (self.quality_input.text or "").strip()

        if not url:
            self._ui_update(text="Enter a valid URL.")
            return

        save_dir = self.base_paths.get(self.path_spinner.text, App.get_running_app().user_data_dir)
        os.makedirs(save_dir, exist_ok=True)

        ydl_opts = {
            "outtmpl": os.path.join(save_dir, "%(title)s.%(ext)s"),
            "noprogress": True,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self.progress_hook],
            "merge_output_format": "mp4",
            "concurrent_fragment_downloads": 1,
        }

        if mode == "Audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": q if q else "192",
                }],
            })
        else:
            if not q or q.lower() == "best":
                ydl_opts["format"] = "bestvideo+bestaudio/best"
            elif q.lower() == "worst":
                ydl_opts["format"] = "worst"
            else:
                ydl_opts["format"] = f"bestvideo[height={q}]+bestaudio/best/best"

        def worker():
            try:
                Clock.schedule_once(lambda dt: self._ui_update(text="Starting..."))
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                Clock.schedule_once(lambda dt: self._ui_update(text=f"Saved to: {save_dir}", pct=100))
            except Exception as e:
                Clock.schedule_once(lambda dt: self._ui_update(text=f"Error: {e}"))

        threading.Thread(target=worker, daemon=True).start()

class YouTubeDownloaderApp(App):
    def build(self):
        return DownloaderUI()

if __name__ == "__main__":
    YouTubeDownloaderApp().run()