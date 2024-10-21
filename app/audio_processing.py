# app/audio_processing.py

import numpy as np
import threading
from scipy.io import wavfile
from scipy.signal import butter, lfilter
import sounddevice as sd

class AudioProcessor:
    def __init__(self):
        self.samplerate = None
        self.original_data = None
        self.duration = None
        self.is_playing = False
        self.is_paused = False
        self.playback_position = 0
        self.audio_lock = threading.Lock()
        self.filter_settings = {
            'low_cut_freq': None,
            'high_cut_freq': None,
            'b': [1.0],  # Default filter coefficients (no filter)
            'a': [1.0]
        }
        self.update_filter_flag = False
        self.stop_flag = False
        self.stream = None
        self.z = None  # Filter state

    def load_audio_file(self, file_path):
        self.samplerate, self.original_data = wavfile.read(file_path)

        # Normalize data
        if self.original_data.dtype == np.int16:
            self.original_data = self.original_data.astype(np.float32) / 32768.0
        elif self.original_data.dtype == np.int32:
            self.original_data = self.original_data.astype(np.float32) / 2147483648.0
        elif self.original_data.dtype == np.uint8:
            self.original_data = (self.original_data.astype(np.float32) - 128) / 128.0
        elif self.original_data.dtype == np.float32:
            pass  # No need to normalize
        else:
            raise ValueError(f"Unsupported audio format: {self.original_data.dtype}")

        self.duration = self.original_data.shape[0] / self.samplerate

    def start_playback(self, finished_callback):
        if not self.is_playing:
            self.is_playing = True
            self.is_paused = False
            self.stop_flag = False
            self.stream = sd.OutputStream(
                samplerate=self.samplerate,
                channels=self.original_data.shape[1] if self.original_data.ndim > 1 else 1,
                callback=self.audio_callback,
                finished_callback=finished_callback
            )
            self.stream.start()

    def pause_playback(self):
        self.is_paused = True

    def resume_playback(self):
        self.is_paused = False

    def stop_playback(self):
        self.stop_flag = True
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def update_filter_settings(self, low_cut_enabled, high_cut_enabled, low_cut_freq, high_cut_freq):
        nyquist = 0.5 * self.samplerate
        low_cut_freq_val = None
        high_cut_freq_val = None
        b = [1.0]
        a = [1.0]

        # Get Low Cut Frequency
        if low_cut_enabled:
            try:
                low_cut_freq_val = float(low_cut_freq)
                if low_cut_freq_val <= 0 or low_cut_freq_val >= nyquist:
                    raise ValueError("Invalid Low Cut Frequency.")
            except ValueError:
                raise ValueError("Invalid Low Cut Frequency.")

        # Get High Cut Frequency
        if high_cut_enabled:
            try:
                high_cut_freq_val = float(high_cut_freq)
                if high_cut_freq_val <= 0 or high_cut_freq_val >= nyquist:
                    raise ValueError("Invalid High Cut Frequency.")
            except ValueError:
                raise ValueError("Invalid High Cut Frequency.")

        # Design Filters
        if low_cut_freq_val and high_cut_freq_val:
            if low_cut_freq_val >= high_cut_freq_val:
                raise ValueError("Low cut frequency must be less than high cut frequency.")
            # Bandpass filter
            Wn = [low_cut_freq_val / nyquist, high_cut_freq_val / nyquist]
            b, a = butter(5, Wn, btype='band')
        elif high_cut_freq_val:
            # Low-pass filter
            Wn = high_cut_freq_val / nyquist
            b, a = butter(5, Wn, btype='low')
        elif low_cut_freq_val:
            # High-pass filter
            Wn = low_cut_freq_val / nyquist
            b, a = butter(5, Wn, btype='high')
        else:
            # No filters
            b = [1.0]
            a = [1.0]

        with self.audio_lock:
            self.filter_settings['low_cut_freq'] = low_cut_freq_val
            self.filter_settings['high_cut_freq'] = high_cut_freq_val
            self.filter_settings['b'] = b
            self.filter_settings['a'] = a
            self.update_filter_flag = True  # Indicate that the filter has been updated
            self.z = None  # Reset filter state

    def audio_callback(self, outdata, frames, time_info, status):
        try:
            if self.stop_flag:
                raise sd.CallbackStop()

            with self.audio_lock:
                if self.is_paused:
                    # Output silence
                    outdata[:] = np.zeros((frames, self.original_data.shape[1] if self.original_data.ndim > 1 else 1))
                    return

                start = int(self.playback_position)
                end = start + frames
                data = self.original_data[start:end]

                # Handle end of audio (looping)
                if len(data) < frames:
                    remaining = frames - len(data)
                    data = np.concatenate((data, self.original_data[0:remaining]))
                    self.playback_position = remaining
                else:
                    self.playback_position += frames

                # Apply filter
                if self.update_filter_flag:
                    # Reinitialize filter state when filter changes
                    self.z = None
                    self.update_filter_flag = False

                b = self.filter_settings['b']
                a = self.filter_settings['a']
                if len(a) > 1 or len(b) > 1:
                    if self.z is None:
                        # Initialize filter state
                        zi_shape = (max(len(a), len(b)) - 1,)
                        if data.ndim > 1:
                            zi_shape += (data.shape[1],)
                        zi = np.zeros(zi_shape)
                        self.z = zi
                    data_filtered, self.z = lfilter(b, a, data, axis=0, zi=self.z)
                else:
                    data_filtered = data

                # Output data
                outdata[:] = data_filtered
        except Exception as e:
            print(f"Error in audio callback: {e}")
            raise

    def seek(self, position):
        with self.audio_lock:
            self.playback_position = int(position * self.original_data.shape[0])
            self.z = None  # Reset filter state

    def get_playback_position(self):
        with self.audio_lock:
            position = (self.playback_position % self.original_data.shape[0]) / self.original_data.shape[0]
        return position

    def save_filtered_audio(self, file_path):
        with self.audio_lock:
            b = self.filter_settings['b']
            a = self.filter_settings['a']
            data = self.original_data.copy()
            data_filtered = lfilter(b, a, data, axis=0)
            # Convert data back to int16
            data_to_save = np.int16(np.clip(data_filtered, -1.0, 1.0) * 32767)
            wavfile.write(file_path, self.samplerate, data_to_save)
