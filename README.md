
# Pig vocalization frequency explorer

Author: Zimu Li MS

Application for filtering audio files. This application allows users to load a WAV file, apply low and high-cut filters, play the audio with real-time filter application, and save the filtered audio. 

## Features

- Load audio files in `.wav` format.
- Apply low-cut and high-cut filters with adjustable cutoff frequencies.
- Real-time playback with filtering.
- Save the filtered audio to a new file.
- Docker support for easy setup and running.

## Prerequisites

Python3 (3.9+) and all dependencies listed in `requirements.txt`.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Nutrition-Health-Neuroscience-DilgerLab/pig_vocalization_frequency_explorer
   cd pig_vocalization_frequency_explorer
   ```

2. Install dependencies using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python -m app.gui
   ```

### Docker

packaging WIP

## Usage

- Use the "Load Audio File" button to open a `.wav` file.
- Use the play button to play the audio and pause to pause it.
- Adjust the low-cut and high-cut filters by enabling the checkboxes and setting the cutoff frequencies.
- Press "Confirm Filter Settings" to apply the selected filters.
- You can save the filtered audio using the "Save Filtered Audio" button.


## Requirements

- `numpy`
- `tkinter`
- `scipy`
- `sounddevice`
