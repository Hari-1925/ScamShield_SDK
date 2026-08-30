from setuptools import setup, find_packages

setup(
    name="scamshield",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pydantic",
        "httpx",
        "numpy",
        "librosa",
        "soundfile",
        "faster-whisper",
        "sentence-transformers",
        "opencv-python",
        "Pillow",
        "scipy",
        "pytesseract",
        "scikit-learn"
    ],
    author="ScamShield Team",
    description="Python SDK for ScamShield multimodal scam and deepfake detection system",
)
