import numpy as np, wave, sys

SR = 44100
BPM = 118
LEN = float(sys.argv[1]) if len(sys.argv) > 1 else 24.0
OUT = sys.argv[2] if len(sys.argv) > 2 else "beat.wav"
beat = 60 / BPM
n = int(LEN * SR)
mix = np.zeros(n + SR, dtype=np.float32)
rng = np.random.default_rng(7)

def add(sig, t, gain=1.0):
    i = int(t * SR)
    if i >= n:
        return
    seg = sig[: n + SR - i]
    mix[i:i + len(seg)] += seg * gain

def env(dur, decay):
    t = np.arange(int(dur * SR)) / SR
    return t, np.exp(-t / decay)

def kick():
    t, e = env(0.45, 0.12)
    f = 45 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * e

def clap():
    t, e = env(0.25, 0.06)
    nz = rng.standard_normal(len(t))
    nz = np.diff(nz, prepend=0)  # brighten
    return nz * e * 0.35

def hat(open_=False):
    t, e = env(0.2 if open_ else 0.06, 0.05 if open_ else 0.012)
    nz = np.diff(np.diff(rng.standard_normal(len(t)), prepend=0), prepend=0)
    return nz * e * 0.08

def lowpass(x, k=6):
    return np.convolve(x, np.ones(k) / k, mode="same")

def pluck(freqs, dur=0.32):
    t, e = env(dur, 0.12)
    s = sum(2 * ((t * f) % 1) - 1 for f in freqs) / len(freqs)
    return lowpass(s, 8) * e

def bass(f, dur):
    t, e = env(dur, dur * 0.7)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sign(np.sin(2 * np.pi * f * t))
    return lowpass(s, 20) * e * np.minimum(1, t / 0.005)

CHORDS = [  # (bass root, chord tones)  Am - F - C - G
    (110.00, [440.00, 523.25, 659.25]),
    (87.31, [349.23, 440.00, 523.25]),
    (130.81, [329.63, 392.00, 523.25]),
    (98.00, [392.00, 493.88, 587.33]),
]
MELODY = [659.25, 0, 587.33, 523.25, 0, 523.25, 440.0, 0]  # little hook, per bar on 8ths

bar = 4 * beat
nbars = int(np.ceil(LEN / bar))
for b in range(nbars):
    t0 = b * bar
    root, chord = CHORDS[b % 4]
    for s in range(8):  # eighths
        t = t0 + s * beat / 2
        swing = 0.03 if s % 2 else 0
        add(hat(open_=(s == 7)), t + swing)
        add(bass(root, beat / 2 * 0.95), t, 0.32 if s % 2 == 0 else 0.22)
        if s in (1, 3, 6):
            add(pluck(chord), t + swing, 0.20)
        if b % 2 == 1 and MELODY[s]:
            add(pluck([MELODY[s] * 2], 0.22), t + swing, 0.10)
    for k in (0, 2.5, 2):
        add(kick(), t0 + k * beat, 0.9)
    for k in (1, 3):
        add(clap(), t0 + k * beat, 1.0)

mix = mix[:n]
fade = int(1.2 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)
mix[: int(0.02 * SR)] *= np.linspace(0, 1, int(0.02 * SR))
mix /= np.abs(mix).max() + 1e-9
stereo = np.stack([mix, mix], 1) * 0.9
w = wave.open(OUT, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((stereo * 32767).astype(np.int16).tobytes()); w.close()
print("ok", LEN)
