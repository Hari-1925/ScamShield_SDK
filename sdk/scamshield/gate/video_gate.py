import os
import cv2
import tempfile
import subprocess
import numpy as np
from scamshield.models import GateResult
from scamshield.gate.image_gate import ImageGate
from scamshield.gate.audio_gate import AudioGate

class VideoGate:
    def __init__(self, image_gate: ImageGate, audio_gate: AudioGate):
        self.image_gate = image_gate
        self.audio_gate = audio_gate

    def run(self, video_bytes: bytes) -> GateResult:
        # Step 1 - Write temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.write(video_bytes)
        tmp.close()
        
        audio_path = tmp.name + ".wav"
        
        try:
            # Step 2 - Extract frames (OpenCV)
            cap = cv2.VideoCapture(tmp.name)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0: fps = 30
            interval = int(fps * 2)
            frame_scores = []
            frame_count = 0
            
            while len(frame_scores) < 10:
                ret, frame = cap.read()
                if not ret: break
                if frame_count % interval == 0:
                    _, buf = cv2.imencode(".jpg", frame)
                    # Only run OCR on the VERY FIRST extracted frame to save massive time
                    do_skip_ocr = len(frame_scores) > 0
                    result = self.image_gate.run(buf.tobytes(), skip_ocr=do_skip_ocr)
                    last_frame_result = result
                    frame_scores.append(result.gate_score)
                frame_count += 1
            cap.release()

            # Step 3 - Extract audio (ffmpeg)
            try:
                subprocess.run([
                    "ffmpeg", "-i", tmp.name,
                    "-vn", "-ar", "16000",
                    "-ac", "1", "-f", "wav",
                    audio_path, "-y", "-loglevel", "quiet"
                ], timeout=30, check=True)
            except Exception as e:
                print(f"FFmpeg extraction failed (may not be installed): {e}")
                
            audio_result = None
            if os.path.exists(audio_path):
                with open(audio_path, "rb") as f:
                    audio_bytes_extracted = f.read()
                if len(audio_bytes_extracted) > 0:
                    audio_result = self.audio_gate.run(audio_bytes_extracted)

            # Step 4 - Fuse
            # Escalate if EITHER the video frames OR the audio track is malicious
            avg_frame = np.mean(frame_scores) if frame_scores else 0.0
            audio_score = audio_result.gate_score if audio_result else 0.0
            gate_score = max(avg_frame, audio_score)

            # Extract semantic tags
            visual_tags = []
            if len(frame_scores) > 0 and 'last_frame_result' in locals():
                visual_tags = last_frame_result.vectors.get("visual_tags", [])
                
            acoustic_tags = []
            if audio_result:
                acoustic_tags = audio_result.vectors.get("acoustic_tags", [])

            return GateResult(
                passed_gate=gate_score >= 0.30,
                gate_score=float(gate_score),
                gate_reason="Video frame and audio analysis",
                vectors={
                    "frame_scores": frame_scores,
                    "avg_frame_score": float(avg_frame),
                    "frames_analysed": len(frame_scores),
                    "audio_score": float(audio_score),
                    "audio_vectors": audio_result.vectors if audio_result else {},
                    "transcription": audio_result.vectors.get("transcription", "") if audio_result else "",
                    "scrubbed_transcription": audio_result.vectors.get("scrubbed_transcription", "") if audio_result else "",
                    "keyword_hits": audio_result.vectors.get("keyword_hits", []) if audio_result else [],
                    "acoustic_tags": acoustic_tags,
                    "visual_tags": visual_tags
                },
                modality="video"
            )
            
        finally:
            # Step 5 - Cleanup
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
            if os.path.exists(audio_path):
                os.remove(audio_path)
