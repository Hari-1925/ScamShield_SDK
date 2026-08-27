import numpy as np
import cv2

class StreamGate:
    """
    Handles real-time chunked processing for live audio and video calls.
    Runs entirely locally with zero cloud calls until gate_threshold is crossed.
    """
    
    def __init__(self, threshold: float = 0.35):
        self.threshold = threshold
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def process_audio_chunk(self, audio_bytes: bytes, chunk_id: int, running_score: float) -> dict:
        # Convert bytes to numpy int16 array
        audio_int = np.frombuffer(audio_bytes, dtype=np.int16)
        # Normalise to float32 -1.0 to 1.0
        audio_float = audio_int.astype(np.float32) / 32768.0

        # Quick acoustic features
        energy = np.abs(audio_float)
        energy_std = float(np.std(energy))
        
        diffs = np.diff(np.sign(audio_float))
        zcr = float(np.mean(np.abs(diffs) / 2))
        
        signal_var = float(np.var(audio_float))

        # Score
        chunk_score = 0.0
        if energy_std < 0.05: chunk_score += 0.30
        if signal_var < 0.001: chunk_score += 0.30
        if zcr < 0.02: chunk_score += 0.25
        if zcr > 0.45: chunk_score += 0.20
        chunk_score = min(chunk_score, 1.0)

        # Update running score
        if chunk_id == 1:
            new_running = chunk_score
        else:
            new_running = (running_score * 0.6 + chunk_score * 0.4)

        return {
            "chunk_score": chunk_score,
            "running_score": new_running,
            "should_forward": (chunk_id % 3 == 0 and new_running >= self.threshold),
            "vectors": {
                "energy_std": energy_std,
                "signal_var": signal_var,
                "zcr": zcr,
                "chunk_id": chunk_id
            }
        }

    def process_video_frame(self, frame_bytes: bytes, audio_bytes: bytes, chunk_id: int, running_score: float) -> dict:
        # Audio quick score
        audio_arr = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        energy_std = float(np.std(np.abs(audio_arr)))
        signal_var = float(np.var(audio_arr))
        zcr = float(np.mean(np.abs(np.diff(np.sign(audio_arr))) / 2))
        
        audio_score = 0.0
        if energy_std < 0.05: audio_score += 0.30
        if signal_var < 0.001: audio_score += 0.30
        if zcr < 0.02: audio_score += 0.25
        if zcr > 0.45: audio_score += 0.20
        audio_score = min(audio_score, 1.0)

        # Face detection
        frame_arr = np.frombuffer(frame_bytes, dtype=np.uint8)
        frame = cv2.imdecode(frame_arr, cv2.IMREAD_COLOR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
        face_detected = len(faces) > 0
        face_score = 0.0

        if face_detected:
            # Crop face region (largest face)
            largest_face = max(faces, key=lambda rect: rect[2] * rect[3])
            x, y, w, h = largest_face
            face_crop = frame[y:y+h, x:x+w]
            
            # Run ELA on face crop
            _, encoded = cv2.imencode('.jpg', face_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
            compressed = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
            
            ela_arr = np.abs(face_crop.astype(int) - compressed.astype(int))
            ela_mean = float(np.mean(ela_arr))
            
            ela_score = 0.0
            if ela_mean > 15: ela_score = 0.30
            
            face_score = ela_score * 0.5

        # Fuse
        chunk_score = (audio_score * 0.6 + face_score * 0.4)

        # Update running score same as audio
        if chunk_id == 1:
            new_running = chunk_score
        else:
            new_running = (running_score * 0.6 + chunk_score * 0.4)

        return {
            "chunk_score": chunk_score,
            "running_score": new_running,
            "should_forward": (chunk_id % 3 == 0 and new_running >= self.threshold),
            "vectors": {
                "audio_score": audio_score,
                "face_score": face_score,
                "face_detected": face_detected,
                "chunk_id": chunk_id
            }
        }
