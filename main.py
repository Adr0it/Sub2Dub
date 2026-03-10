import subprocess
import queue
import threading
import soundfile as sf
import numpy as np
import tempfile
import webvtt
import argparse
import re
from pathlib import Path

# Piper Model
MODEL = "en_US-libritts-high.onnx"

tts_queue = queue.PriorityQueue()
clips = []
samplerate = None

def is_speakable(text):
    return re.search(r"[A-Za-z0-9]", text) is not None

def parse_time(ts):
    """Convert 'HH:MM:SS.mmm' or 'MM:SS.mmm' to seconds as float."""
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = parts
    elif len(parts) == 2:
        h = 0
        m, s = parts
    else:
        raise ValueError(f"Invalid timestamp: {ts}")
    return int(h)*3600 + int(m)*60 + float(s)

def generate_tts(text):
    temp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)

    # Can change Piper model's parameters for different voiceover
    subprocess.run(
        ["piper", "--model", MODEL, "--speaker", str(473), "--length_scale", str(0.95), "--noise_scale", str(0.5), "--noise_w", str(0.7), "--output_file", temp.name],
        input=text.encode(),
    )
    return temp.name

def producer(subtitle_file):
    if (".srt" in subtitle_file):
        webvtt.from_srt(subtitle_file).save()
        vtt = subtitle_file[0:subtitle_file.index(".srt")] + ".vtt"
    else:
        vtt = subtitle_file 
    
    for caption in webvtt.read(vtt):
        if not is_speakable(caption.text):
            print("Skipping non-speech:", caption.text)
            continue

        print("Generating:", caption.text)

        audio_file = generate_tts(caption.text)
        tts_queue.put((parse_time(caption.start), audio_file))
    
def consumer():
    global samplerate

    while True:
        start_time, audio_file = tts_queue.get()
        data, sr = sf.read(audio_file)

        if samplerate is None:
            samplerate = sr

        clips.append((start_time, data))
        tts_queue.task_done()

def build_final_audio(output_loc):
    global samplerate

    if not clips:
        print("No clips to combine!")
        return

    clips.sort(key=lambda x: x[0])

    placed_clips = []
    cur_end = 0

    for start_time, data in clips:
        start_sample = int(start_time * samplerate)

        actual_start = max(start_sample, cur_end)
        actual_end = actual_start + len(data)

        placed_clips.append((actual_start, data))
        cur_end = actual_end

    final_audio = np.zeros(cur_end, dtype=np.float32)

    for start_sample, data in placed_clips:
        final_audio[start_sample:start_sample + len(data)] = data

    sf.write(output_loc, final_audio, samplerate)
    print(f"Final audio written: {output_loc}")

def run(subtitle_file, output_loc = Path.home() / "OneDrive" / "Desktop" / "out.wav"):
    producer_thread = threading.Thread(target=producer, args=(subtitle_file,))
    consumer_thread = threading.Thread(target=consumer, daemon=True)

    producer_thread.start()
    consumer_thread.start()

    producer_thread.join()

    tts_queue.join()

    build_final_audio(output_loc)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sub2Dub")
    parser.add_argument("subtitle_file", help="Path to subtitle file (.vtt/.srt)")
    parser.add_argument(
        "output_loc",
        nargs="?",
        default=Path.home() / "OneDrive" / "Desktop" / "out.wav",
        help="Output audio file (default: Desktop/out.wav)"
    )
    args = parser.parse_args()
    
    run(args.subtitle_file, args.output_loc)