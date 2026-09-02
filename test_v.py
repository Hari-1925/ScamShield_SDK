import os
import cv2
import json
from sdk.scamshield.gate.video_gate import VideoGate
from sdk.scamshield.gate.audio_gate import AudioGate
from sdk.scamshield.gate.image_gate import ImageGate
from sdk.scamshield.gate.text_gate import TextGate

text = TextGate()
text.load()
img = ImageGate(text)
img.load()
audio = AudioGate(text)
audio.load()
video = VideoGate(img, audio)

path = os.path.join('tests', 'samples', 'Video', 'deepfake_videocall.mp4')
print('Testing deepfake_videocall.mp4...')
res = video.run(open(path, 'rb').read(), contact_id='unknown')
print('Gate passed:', res.passed_gate)
print('Score:', res.gate_score)
print('Face swap score:', res.vectors.get('face_swap_score'))
print('Transcription:', res.vectors.get('audio_vectors', {}).get('transcription'))
print('Text score:', res.vectors.get('audio_vectors', {}).get('text_score'))
