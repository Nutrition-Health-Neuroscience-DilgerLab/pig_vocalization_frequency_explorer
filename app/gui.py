# app/gui.py

import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time
import os
from .audio_processing import AudioProcessor

class AudioFilterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Filter Application")

        # Initialize variables
        self.audio_processor = AudioProcessor()
        self.is_playing = False
        self.is_paused = False
        self.duration = None
        self.file_name = None  # Store the name of the loaded file

        # GUI Elements
        self.create_widgets()

    def create_widgets(self):
        # Load Button
        self.load_button = tk.Button(self.root, text="Load Audio File", command=self.load_audio)
        self.load_button.pack(pady=5)

        # File Name Label
        self.file_label = tk.Label(self.root, text="No file loaded")
        self.file_label.pack(pady=5)

        # Play and Pause Buttons
        self.play_button = tk.Button(self.root, text="Play", command=self.play_audio, state='disabled')
        self.play_button.pack(pady=5)

        self.pause_button = tk.Button(self.root, text="Pause", command=self.pause_audio, state='disabled')
        self.pause_button.pack(pady=5)

        # Low Cut Filter
        self.low_cut_frame = tk.Frame(self.root)
        self.low_cut_frame.pack(pady=5)

        self.low_cut_var = tk.BooleanVar()
        self.low_cut_check = tk.Checkbutton(self.low_cut_frame, text="Enable Low Cut Filter", variable=self.low_cut_var)
        self.low_cut_check.pack(side='left')

        self.low_cut_label = tk.Label(self.low_cut_frame, text="Cut-off Frequency (Hz):")
        self.low_cut_label.pack(side='left')

        self.low_cut_entry = tk.Entry(self.low_cut_frame, width=10)
        self.low_cut_entry.insert(0, "2000")
        self.low_cut_entry.pack(side='left')

        # High Cut Filter
        self.high_cut_frame = tk.Frame(self.root)
        self.high_cut_frame.pack(pady=5)

        self.high_cut_var = tk.BooleanVar()
        self.high_cut_check = tk.Checkbutton(self.high_cut_frame, text="Enable High Cut Filter", variable=self.high_cut_var)
        self.high_cut_check.pack(side='left')

        self.high_cut_label = tk.Label(self.high_cut_frame, text="Cut-off Frequency (Hz):")
        self.high_cut_label.pack(side='left')

        self.high_cut_entry = tk.Entry(self.high_cut_frame, width=10)
        self.high_cut_entry.insert(0, "5000")
        self.high_cut_entry.pack(side='left')

        # Confirm Button for Filter Settings
        self.confirm_button = tk.Button(self.root, text="Confirm Filter Settings", command=self.update_filter)
        self.confirm_button.pack(pady=5)

        # Progress Scale (for seeking)
        self.progress_var = tk.DoubleVar()
        self.progress_scale = tk.Scale(self.root, variable=self.progress_var, orient='horizontal', length=400,
                                       from_=0, to=100, state='disabled')
        self.progress_scale.pack(pady=5)
        self.progress_scale.bind("<ButtonRelease-1>", self.seek_audio)

        # Time Label
        self.time_label = tk.Label(self.root, text="00:00 / 00:00")
        self.time_label.pack(pady=5)

        # Save Button
        self.save_button = tk.Button(self.root, text="Save Filtered Audio", command=self.save_audio, state='disabled')
        self.save_button.pack(pady=5)

    def load_audio(self):
        file_path = filedialog.askopenfilename(filetypes=[("WAV Files", "*.wav *.WAV")])
        if file_path:
            try:
                self.audio_processor.load_audio_file(file_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load audio file: {e}")
                return

            self.play_button.config(state='normal')
            self.save_button.config(state='normal')
            self.duration = self.audio_processor.duration
            total_time_str = time.strftime('%M:%S', time.gmtime(self.duration))
            self.time_label.config(text=f"00:00 / {total_time_str}")

            # Update the file name label
            self.file_name = os.path.basename(file_path)
            self.file_label.config(text=f"File: {self.file_name}")

            # Optionally, update the window title
            self.root.title(f"Audio Filter Application - {self.file_name}")

    def play_audio(self):
        if not self.is_playing:
            self.is_playing = True
            self.is_paused = False
            self.pause_button.config(text="Pause", state='normal')
            self.progress_scale.config(state='normal')
            self.update_filter()  # Apply the initial filter settings
            self.audio_processor.start_playback(self.playback_finished)
            self.update_progress()

    def pause_audio(self):
        if self.is_playing and not self.is_paused:
            # Pause playback
            self.is_paused = True
            self.pause_button.config(text="Resume")
            self.audio_processor.pause_playback()
        elif self.is_playing and self.is_paused:
            # Resume playback
            self.is_paused = False
            self.pause_button.config(text="Pause")
            self.audio_processor.resume_playback()

    def update_filter(self):
        low_cut_enabled = self.low_cut_var.get()
        high_cut_enabled = self.high_cut_var.get()
        low_cut_freq = self.low_cut_entry.get()
        high_cut_freq = self.high_cut_entry.get()

        try:
            self.audio_processor.update_filter_settings(
                low_cut_enabled=low_cut_enabled,
                high_cut_enabled=high_cut_enabled,
                low_cut_freq=low_cut_freq,
                high_cut_freq=high_cut_freq
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

    def seek_audio(self, event):
        if self.is_playing:
            position = self.progress_var.get() / 100
            self.audio_processor.seek(position)
            self.update_progress()

    def update_progress(self):
        if self.is_playing:
            position = self.audio_processor.get_playback_position()
            progress = position * 100
            self.progress_var.set(progress)

            # Update time label
            current_time = position * self.duration
            total_time = self.duration
            current_time_str = time.strftime('%M:%S', time.gmtime(current_time))
            total_time_str = time.strftime('%M:%S', time.gmtime(total_time))
            self.time_label.config(text=f"{current_time_str} / {total_time_str}")

            self.root.after(100, self.update_progress)
        else:
            self.progress_var.set(0)
            self.time_label.config(text="00:00 / 00:00")

    def playback_finished(self):
        # Schedule GUI updates in the main thread
        self.root.after(0, self.update_gui_on_finish)

    def update_gui_on_finish(self):
        self.is_playing = False
        self.is_paused = False
        self.pause_button.config(state='disabled', text="Pause")
        self.progress_scale.config(state='disabled')
        self.progress_var.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def save_audio(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                 filetypes=[("WAV Files", "*.wav")])
        if file_path:
            try:
                self.audio_processor.save_filtered_audio(file_path)
                messagebox.showinfo("Saved", "Filtered audio saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save audio file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioFilterApp(root)
    root.mainloop()
