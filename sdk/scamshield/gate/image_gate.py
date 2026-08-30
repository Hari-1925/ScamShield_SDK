import os
import io
import cv2
import numpy as np
import scipy.ndimage
from PIL import Image
from scamshield.models import GateResult
from scamshield.gate.text_gate import TextGate

class ImageGate:
    def __init__(self, text_gate: TextGate):
        self.face_cascade = None
        self.text_gate = text_gate

    def load(self):
        # Load OpenCV haar cascade
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        print("Image gate loaded")

    def run(self, image_bytes: bytes, skip_ocr: bool = False) -> GateResult:
        import pytesseract
        
        # Step 1 - Load & Resize (MASSIVE SPEEDUP)
        img = Image.open(io.BytesIO(image_bytes))
        img_rgb = img.convert("RGB")
        
        # Max dimension 1024 to speed up Tesseract and ELA by 10x
        if max(img_rgb.size) > 1024:
            img_rgb.thumbnail((1024, 1024), Image.Resampling.LANCZOS)

        # Step 2 - ELA
        buffer = io.BytesIO()
        img_rgb.save(buffer, "JPEG", quality=90)
        buffer.seek(0)
        compressed = Image.open(buffer)
        
        arr_orig = np.array(img_rgb).astype(int)
        arr_comp = np.array(compressed).astype(int)
            
        ela_arr = np.abs(arr_orig - arr_comp)
        ela_mean = float(np.mean(ela_arr))
        ela_std  = float(np.std(ela_arr))
        ela_max  = float(np.max(ela_arr))

        # Step 3 - ELA score
        ela_score = 0.0
        if ela_mean > 15: ela_score += 0.30
        if ela_std  > 12: ela_score += 0.20
        if ela_max  > 80: ela_score += 0.15

        # Step 4 - Noise analysis
        gray = np.array(img_rgb.convert("L")).astype(float)
        blurred = scipy.ndimage.uniform_filter(gray, size=3)
        noise = gray - blurred
        noise_std = float(np.std(noise))
        # H.264 compression lowers noise_std to ~2.0. True GANs are often < 1.2
        noise_score = 0.20 if noise_std < 1.2 else 0.0

        # Step 5 - OCR
        tess_path = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = tess_path
        
        ocr_text = ""
        ocr_score = 0.0
        ocr_result = None
        
        if not skip_ocr:
            try:
                ocr_text = pytesseract.image_to_string(img_rgb)
                if ocr_text.strip():
                    ocr_result = self.text_gate.run(ocr_text)
                    ocr_score = ocr_result.gate_score
            except Exception as e:
                print(f"OCR failed (Tesseract may not be installed): {e}")

        # Step 6 - Face detection
        cv_img = cv2.cvtColor(np.array(img_rgb), cv2.COLOR_RGB2BGR)
        gray_cv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
        
        faces = []
        if self.face_cascade:
            faces = self.face_cascade.detectMultiScale(gray_cv, 1.1, 5, minSize=(30, 30))
        face_detected = len(faces) > 0

        # Step 7 - Semantic Feature Abstraction (Visual Tags)
        visual_tags = []
        if ela_mean > 15 or ela_max > 80:
            visual_tags.append("Lighting consistency: Artificial/Mismatched shadows (High ELA)")
        else:
            visual_tags.append("Lighting consistency: Natural shadows")
            
        if noise_std < 1.2:
            visual_tags.append("Pixel texture: Unnaturally smooth (GAN/AI generation)")
            
        if face_detected and (ela_mean > 15):
            visual_tags.append("Face region: Significant digital manipulation detected (Deepfake Face-Swap likely)")

        # Step 8 - Fuse
        # Use max instead of average so that if EITHER the image is manipulated
        # OR the text in the image contains a scam, it escalates.
        image_threat = min(ela_score + noise_score, 1.0)
        gate_score = max(image_threat, ocr_score)

        return GateResult(
            passed_gate=gate_score >= 0.30,
            gate_score=float(gate_score),
            gate_reason="Image forensics and OCR analysis",
            vectors={
                "ela_mean": ela_mean,
                "ela_std": ela_std,
                "ela_max": ela_max,
                "noise_std": noise_std,
                "face_detected": face_detected,
                "visual_tags": visual_tags,
                "ocr_text": ocr_text,
                "ocr_score": ocr_score,
                "ocr_vectors": ocr_result.vectors if ocr_result else {}
            },
            modality="image"
        )
