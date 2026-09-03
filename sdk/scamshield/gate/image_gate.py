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

    def run(self, image_bytes: bytes, skip_ocr: bool = False, contact_id: str = "unknown", is_video_frame: bool = False, is_saved_contact: bool = False) -> GateResult:
        import numpy as np
        import cv2
        import io
        from PIL import Image, ImageChops, ImageEnhance
        import pytesseract

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img_rgb = img.convert("RGB")
        except Exception as e:
            return GateResult(
                passed_gate=False, gate_score=0.0, gate_reason="Corrupt or Unsupported Image",
                vectors={}, modality="image"
            )
        
        # Max dimension 1024 to speed up Tesseract and ELA by 10x
        if max(img_rgb.size) > 1024:
            img_rgb.thumbnail((1024, 1024))
            
        ocr_text = ""
        ocr_score = 0.0
        ocr_result = None
        
        if not skip_ocr:
            try:
                ocr_text = pytesseract.image_to_string(img_rgb).strip()
                if ocr_text:
                    # Pass the contact_id for Historical RAG Trust checks on OCR text!
                    ocr_result = self.text_gate.run(ocr_text, contact_id=contact_id, is_saved_contact=is_saved_contact)
                    ocr_score = ocr_result.gate_score
            except Exception as e:
                print(f"OCR failed (Tesseract may not be installed): {e}")

        # Step 2 - ELA (Error Level Analysis for Forgery)
        ela_score = 0.0
        ela_mean = ela_std = ela_max = 0.0
        
        # Disable ELA for video frames because H264 compression naturally causes massive JPEG block artifacts
        if not is_video_frame:
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
            if ela_mean > 15: ela_score += 0.30
            if ela_std  > 12: ela_score += 0.20
            if ela_max  > 80: ela_score += 0.15

        # Step 4 - Frequency & Noise analysis (FFT) for AI/GAN detection
        gray = np.array(img_rgb.convert("L")).astype(float)
        
        # Fast 2D FFT to find high-frequency spectral artifacts common in GANs
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1)
        # Compute ratio of high frequencies (edges/noise) to low frequencies (structure)
        h, w = gray.shape
        center_h, center_w = h // 2, w // 2
        # Mask out low frequencies
        mask = np.ones((h, w))
        r = min(h, w) // 4
        y, x = np.ogrid[-center_h:h-center_h, -center_w:w-center_w]
        mask[x**2 + y**2 <= r**2] = 0
        high_freq_mag = np.mean(magnitude_spectrum * mask)
        
        # Unnaturally low high-frequency magnitude means smooth/plastic texture (Diffusion/GANs)
        noise_score = 0.25 if high_freq_mag < 100 else 0.0

        # Step 5 - OCR -> TextGate CAHS V2
        tess_path = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
        pytesseract.pytesseract.tesseract_cmd = tess_path
        
        ocr_text = ""
        ocr_score = 0.0
        ocr_result = None
        
        if not skip_ocr:
            try:
                ocr_text = pytesseract.image_to_string(img_rgb).strip()
                if ocr_text:
                    # Pass the contact_id for Historical RAG Trust checks on OCR text!
                    is_saved = contact_id != "unknown"
                    ocr_result = self.text_gate.run(ocr_text, contact_id=contact_id, is_saved_contact=is_saved)
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
            visual_tags.append("Forgery: Spliced text or mismatched JPEG blocks (Fake Receipt/Document)")
            
        if noise_score > 0:
            visual_tags.append("Texture: Unnaturally smooth frequency distribution (AI Generated Fake Person)")
            
        if face_detected and (ela_mean > 15):
            visual_tags.append("Face region: Significant digital manipulation detected")

        # Step 8 - Fuse
        # ELA + Frequency gives image_threat. 
        # OCR gives semantic threat. We escalate if EITHER is malicious.
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
                "noise_std": float(high_freq_mag), # Map it back so cloud doesn't break
                "face_detected": face_detected,
                "visual_tags": visual_tags,
                "ocr_text": ocr_text,
                "ocr_score": ocr_score,
                "ocr_vectors": ocr_result.vectors if ocr_result else {}
            },
            modality="image"
        )
