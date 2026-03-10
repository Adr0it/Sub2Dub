<img src="Sub2Dub.png">

A simple program that converts subtitles (.srt, .vtt) to an AI voiceover (.wav) using Piper TTS.

### Instructions:
Install all the necessary libraries with: 
```
pip install -r requirements.txt
```

Then run
```
python main.py subtitle_file
```
for a default output location of Desktop, or
```
python main.py subtitle_file output_loc
```
for a specific output location.

## Note:
You can customize the included Piper model (by changing speakers for example) or import your own Piper model. Currently, an English AI voiceover is generated, but with different models, AI voiceovers in different languages is possible.

## References:
The libritts (high) model is used: https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/en/en_US/libritts/high
