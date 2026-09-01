import librosa
import numpy as np

def analyze(path):
    y, sr = librosa.load(path, sr=16000)
    rms = np.mean(librosa.feature.rms(y=y)[0])
    
    pitches, _ = librosa.piptrack(y=y, sr=sr)
    p_vals = pitches[pitches > 0]
    p_std = np.std(p_vals) if len(p_vals) > 0 else 0
    
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    f_var = np.var(onset_env)
    
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
    m_std = np.mean(np.std(mfcc, axis=1))
    
    print(f"File: {path} | RMS: {rms:.4f} | PitchStd: {p_std:.2f} | FluxVar: {f_var:.2f} | MfccStd: {m_std:.2f}")

analyze('tests/samples/tts.mp3')
analyze('tests/samples/irl_scam.mp3')
analyze('tests/samples/normal.mp3')
