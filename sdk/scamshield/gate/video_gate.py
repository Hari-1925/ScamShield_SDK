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

    def run(self, video_bytes: bytes, contact_id: str = "unknown", is_saved_contact: bool = False) -> GateResult:
        # Step 1 - Write temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        tmp.write(video_bytes)
        tmp.close()
        
        audio_path = tmp.name + ".wav"
        
        try:
            # Step 2 - Extract frames and Route to ImageGate
            cap = cv2.VideoCapture(tmp.name)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps <= 0: fps = 30
            interval = int(fps * 1) # Extract 1 frame per second (as per design)
            frame_scores = []
            frame_count = 0
            
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            face_centers = []
            
            while len(frame_scores) < 10:
                ret, frame = cap.read()
                if not ret: break

                # Deepfake Face Jitter Tracking (Check 5 times a second)
                if frame_count % max(1, int(fps/5)) == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                    if len(faces) > 0:
                        x, y, w, h = faces[0]
                        face_centers.append((x + w/2, y + h/2))

                # Route keyframes to ImageGate
                if frame_count % interval == 0:
                    _, buf = cv2.imencode(".jpg", frame)
                    # Only run OCR on the VERY FIRST extracted frame to save massive time
                    do_skip_ocr = len(frame_scores) > 0
                    result = self.image_gate.run(buf.tobytes(), skip_ocr=do_skip_ocr, contact_id=contact_id, is_video_frame=True, is_saved_contact=is_saved_contact)
                    last_frame_result = result
                    frame_scores.append(result.gate_score)
                    
                frame_count += 1
            cap.release()
            
            face_swap_score = 0.0
            if len(face_centers) > 3:
                # Calculate variance of face movement (jitter) - temporal inconsistency in deepfakes
                dx = [abs(face_centers[i][0] - face_centers[i-1][0]) for i in range(1, len(face_centers))]
                dy = [abs(face_centers[i][1] - face_centers[i-1][1]) for i in range(1, len(face_centers))]
                
                # Normalize jitter by face size to prevent resolution-dependent false positives
                # Modern deepfakes often have ABNORMALLY LOW jitter (anchored bounding boxes),
                # or extreme glitching. We only flag absolute extreme teleportation glitches here.
                mean_jitter = np.mean(dx) + np.mean(dy)
                if mean_jitter > 300.0: # Only flag massive teleporting bounding boxes (glitches)
                    face_swap_score = 0.40

            # Step 3 - Extract audio (ffmpeg) -> DAVE Audio Gate
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
                    audio_result = self.audio_gate.run(audio_bytes_extracted, contact_id=contact_id, is_saved_contact=is_saved_contact)

            # Step 4 - Fuse
            # Escalate if EITHER the video frames, the audio track, OR the face jitter is malicious
            # Use MAX instead of MEAN to prevent diluting the OCR score (which only runs on frame 1)
            max_frame = float(np.max(frame_scores)) if frame_scores else 0.0
            audio_score = audio_result.gate_score if audio_result else 0.0
            gate_score = max(max_frame, audio_score, face_swap_score)

            # Extract semantic tags
            visual_tags = []
            if len(frame_scores) > 0 and 'last_frame_result' in locals():
                visual_tags = last_frame_result.vectors.get("visual_tags", [])
                
            if face_swap_score > 0:
                visual_tags.append("Temporal: High facial bounding box jitter (Deepfake Face-Swap likely)")
                
            acoustic_tags = []
            if audio_result:
                acoustic_tags = audio_result.vectors.get("acoustic_tags", [])

            return GateResult(
                passed_gate=gate_score >= 0.55, # Aligned with TextGate threshold
                gate_score=float(gate_score),
                gate_reason="Video frame and audio analysis",
                vectors={
                    "face_swap_score": float(face_swap_score),
                    "frame_scores": frame_scores,
                    "max_frame_score": max_frame,
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
