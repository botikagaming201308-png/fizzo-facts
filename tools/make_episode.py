import json, math, os, random, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.expanduser("~/kokoro")
EP_PATH = sys.argv[1]
EP = json.load(open(EP_PATH))
OUT = os.path.expanduser("~/fizzo_build/" + EP["id"] + "/")
os.makedirs(OUT, exist_ok=True)
W, H, FPS, SR = 1080, 1920, 30, 24000
FONT = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
F = lambda n: ImageFont.truetype(FONT, n)

FIZZO = dict(name="FIZZO", voice="am_puck", speed=1.12, color=(60, 220, 255))
GIZMO = dict(name="GIZMO JR.", voice="bm_george", speed=1.0, color=(255, 150, 40))

# episode JSON: {"id","title","description","tags",[...],"beats":[{"speaker":"fizzo|gizmo","caption","phonemes","gizmo_mood","fizzo_mood","flash"?}]}
SPK = {"fizzo": FIZZO, "gizmo": GIZMO}
BEATS = [(SPK[b["speaker"]], b["caption"], b["phonemes"], b.get("gizmo_mood", "idle"), b.get("fizzo_mood", "idle")) for b in EP["beats"]]
FLASH = {i for i, b in enumerate(EP["beats"]) if b.get("flash")}
GAP = 0.22
COVER = 1.5  # seconds of end card (hook text) so the last frame / chosen cover sells the episode

def cover_text():
    # optional "cover" field; default = title without hashtags and emoji
    t = EP.get("cover") or " ".join(w for w in EP["title"].split() if not w.startswith("#"))
    return "".join(ch for ch in t if ord(ch) < 0x2000).strip()

# ---------- voice ----------
def make_voices():
    import onnxruntime as rt
    vocab = json.load(open(os.path.join(HERE, "vocab.json")))["vocab"]
    voices = np.load(os.path.join(MODEL_DIR, "voices.bin"))
    sess = rt.InferenceSession(os.path.join(MODEL_DIR, "kokoro.onnx"), providers=["CPUExecutionProvider"])
    names = {i.name: i.type for i in sess.get_inputs()}
    tok = "input_ids" if "input_ids" in names else "tokens"
    clips = []
    for i, (spk, cap, ph, *_) in enumerate(BEATS):
        miss = {c for c in ph if c not in vocab}
        if miss:
            raise SystemExit(f"beat {i}: phoneme characters not in vocab: {miss}")
        toks = [vocab[c] for c in ph if c in vocab]
        feed = {tok: np.array([[0, *toks, 0]], dtype=np.int64),
                "style": np.asarray(voices[spk["voice"]][len(toks)], dtype=np.float32),
                "speed": np.array([spk["speed"]], dtype=np.int32 if "int" in names["speed"] else np.float32)}
        a = sess.run(None, feed)[0].squeeze().astype(np.float32)
        # trim silence at ends
        idx = np.where(np.abs(a) > 0.01)[0]
        a = a[max(0, idx[0] - 600): idx[-1] + 1200]
        clips.append(a)
    np.save(OUT + "clips.npy", np.array(clips, dtype=object), allow_pickle=True)
    return clips

# ---------- drawing ----------
INK = (40, 45, 65)
ACC = (255, 214, 0)

def bg(top=(30, 15, 70), bot=(8, 6, 28)):
    a = np.linspace(0, 1, H)[:, None]
    img = (np.array(top)[None, None, :] * (1 - a[..., None]) + np.array(bot)[None, None, :] * a[..., None])
    img = np.repeat(img, W, axis=1).astype(np.uint8)
    return Image.fromarray(img, "RGB")

def eye(d, x, y, r, mood, t, col):
    if mood in ("happy", "laugh"):
        d.arc([x - r, y - r, x + r, y + r * 0.8], 200, 340, fill=col, width=int(r * 0.35))
    elif mood == "smug":
        d.chord([x - r, y - r, x + r, y + r], 0, 180, fill=col)
    elif mood == "glitch":
        d.line([x - r, y - r, x + r, y + r], fill=(255, 60, 60), width=int(r * 0.4))
        d.line([x - r, y + r, x + r, y - r], fill=(255, 60, 60), width=int(r * 0.4))
    else:
        rr = r * (1.25 if mood == "shock" else 1)
        if (t % 2.6) < 0.1:
            d.rounded_rectangle([x - rr, y - 6, x + rr, y + 6], radius=6, fill=col)
        else:
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=col)
            d.ellipse([x - rr * 0.1, y - rr * 0.6, x + rr * 0.4, y - rr * 0.1], fill=(255, 255, 255))

def draw_fizzo(img, cx, cy, s, t, mood, mouth, active):
    d = ImageDraw.Draw(img)
    cy += math.sin(t * 6) * 12 * s - (abs(math.sin(t * 14)) * 30 * s if mood == "laugh" else 0)
    col = (80, 225, 255)
    d.ellipse([cx - 140*s, cy + 330*s, cx + 140*s, cy + 365*s], fill=(5, 4, 15))
    d.rounded_rectangle([cx - 115*s, cy + 120*s, cx + 115*s, cy + 320*s], radius=50*s, fill=(215, 240, 250), outline=INK, width=int(8*s))
    d.ellipse([cx - 32*s, cy + 185*s, cx + 32*s, cy + 249*s], fill=col, outline=INK, width=int(6*s))
    wave_ = math.sin(t * 9) * 30 * s if active else 0
    for side in (-1, 1):
        hx, hy = cx + side * 195*s, cy + 130*s - (wave_ if side < 0 else -wave_ * 0.3)
        d.line([cx + side * 115*s, cy + 175*s, hx, hy], fill=INK, width=int(17*s))
        d.ellipse([hx - 26*s, hy - 26*s, hx + 26*s, hy + 26*s], fill=(215, 240, 250), outline=INK, width=int(6*s))
    # antenna + fizz bubbles
    d.line([cx, cy - 170*s, cx, cy - 235*s], fill=INK, width=int(10*s))
    d.ellipse([cx - 24*s, cy - 259*s, cx + 24*s, cy - 211*s], fill=col, outline=INK, width=int(6*s))
    for k in range(5):
        ph = (t * 0.9 + k * 0.21) % 1
        bx = cx + math.sin(k * 2.3 + t * 3) * 40*s
        by = cy - 260*s - ph * 170*s
        r = (8 + k * 3) * s * (1 - ph * 0.5)
        d.ellipse([bx - r, by - r, bx + r, by + r], outline=col, width=max(2, int(4*s)))
    d.rounded_rectangle([cx - 185*s, cy - 170*s, cx + 185*s, cy + 120*s], radius=80*s, fill=(230, 245, 252), outline=INK, width=int(10*s))
    d.rounded_rectangle([cx - 148*s, cy - 132*s, cx + 148*s, cy + 82*s], radius=58*s, fill=(20, 28, 45))
    for ex in (-62, 62):
        eye(d, cx + ex*s, cy - 38*s, 38*s, mood, t, col)
    h = (10 + 50 * mouth) * s
    if mood in ("happy", "laugh") and mouth < 0.1:
        d.arc([cx - 50*s, cy - 10*s, cx + 50*s, cy + 55*s], 20, 160, fill=col, width=int(12*s))
    else:
        d.rounded_rectangle([cx - 46*s, cy + 22*s, cx + 46*s, cy + 22*s + h], radius=16*s, fill=col)

def draw_gizmo(img, cx, cy, s, t, mood, mouth, active):
    d = ImageDraw.Draw(img)
    if mood == "glitch":
        cx += random.uniform(-14, 14) * s
    bob = math.sin(t * 5 + 1) * 10 * s
    if mood == "shock":
        bob -= 20 * s
    cy += bob
    body = (255, 170, 70)
    d.ellipse([cx - 120*s, cy + 290*s, cx + 120*s, cy + 322*s], fill=(5, 4, 15))
    d.rounded_rectangle([cx - 95*s, cy + 110*s, cx + 95*s, cy + 285*s], radius=40*s, fill=body, outline=INK, width=int(8*s))
    # bow tie
    d.polygon([(cx, cy + 135*s), (cx - 45*s, cy + 112*s), (cx - 45*s, cy + 158*s)], fill=(200, 40, 60), outline=INK)
    d.polygon([(cx, cy + 135*s), (cx + 45*s, cy + 112*s), (cx + 45*s, cy + 158*s)], fill=(200, 40, 60), outline=INK)
    d.ellipse([cx - 12*s, cy + 123*s, cx + 12*s, cy + 147*s], fill=(230, 60, 80), outline=INK)
    arm = -40 * s if mood == "shock" else 0
    for side in (-1, 1):
        hx, hy = cx + side * 160*s, cy + 220*s + (arm if mood == "shock" else 0) - (side > 0 and active) * 70*s
        d.line([cx + side * 95*s, cy + 170*s, hx, hy], fill=INK, width=int(15*s))
        d.ellipse([hx - 22*s, hy - 22*s, hx + 22*s, hy + 22*s], fill=body, outline=INK, width=int(5*s))
    # propeller cap
    d.chord([cx - 70*s, cy - 205*s, cx + 70*s, cy - 120*s], 180, 360, fill=(60, 120, 230), outline=INK, width=int(6*s))
    d.line([cx, cy - 205*s, cx, cy - 235*s], fill=INK, width=int(7*s))
    spin = math.cos(t * (40 if mood == "glitch" else 12))
    d.ellipse([cx - 60*s * abs(spin) - 4, cy - 248*s, cx + 60*s * abs(spin) + 4, cy - 228*s], fill=(255, 214, 0), outline=INK, width=int(4*s))
    # round head
    d.ellipse([cx - 165*s, cy - 165*s, cx + 165*s, cy + 125*s], fill=(255, 190, 100), outline=INK, width=int(10*s))
    d.ellipse([cx - 130*s, cy - 125*s, cx + 130*s, cy + 90*s], fill=(28, 22, 32))
    ecol = (255, 200, 90)
    for ex in (-55, 55):
        eye(d, cx + ex*s, cy - 25*s, 30*s, mood, t, ecol)
        # glasses
        d.rounded_rectangle([cx + ex*s - 50*s, cy - 70*s, cx + ex*s + 50*s, cy + 20*s], radius=14*s, outline=(240, 240, 255), width=int(7*s))
    d.line([cx - 5*s, cy - 30*s, cx + 5*s, cy - 30*s], fill=(240, 240, 255), width=int(7*s))
    if mood == "shock" and mouth < 0.1:
        d.ellipse([cx - 20*s, cy + 35*s, cx + 20*s, cy + 80*s], fill=ecol)
    elif mood == "smug" and mouth < 0.1:
        d.arc([cx - 40*s, cy + 10*s, cx + 50*s, cy + 60*s], 20, 120, fill=ecol, width=int(10*s))
    else:
        h = (8 + 40 * mouth) * s
        d.rounded_rectangle([cx - 36*s, cy + 35*s, cx + 36*s, cy + 35*s + h], radius=12*s, fill=ecol)

def wrap(d, words, f, maxw):
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if cur and d.textlength(test, font=f) > maxw:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(cur)
    return lines

def caption(img, spk, text, prog, t, size=None):
    d = ImageDraw.Draw(img)
    words = text.split()
    size = size or (104 if len(text) < 40 else (88 if len(text) < 60 else 78))
    f = F(size)
    lines = wrap(d, words, f, W - 140)
    lh = int(size * 1.3)
    y0 = 610 - len(lines) * lh // 2
    # speaker tag
    if spk is not None:
        tag = F(52)
        tw = d.textlength(spk["name"], font=tag)
        d.rounded_rectangle([W/2 - tw/2 - 28, y0 - 115, W/2 + tw/2 + 28, y0 - 35], radius=40, fill=spk["color"])
        d.text((W/2, y0 - 75), spk["name"], font=tag, fill=(15, 15, 25), anchor="mm")
    shown = int(math.ceil(prog * len(words) + 0.001))
    k = 0
    space = d.textlength(" ", font=f)
    for li, ln in enumerate(lines):
        widths = [d.textlength(w, font=f) for w in ln]
        x = (W - sum(widths) - space * (len(ln) - 1)) / 2
        y = y0 + li * lh
        for w, wd in zip(ln, widths):
            if k < shown:
                core = w.strip(".,!?:;")
                hl = len(core) > 1 and core.isupper() or core.isdigit()
                if hl:
                    d.rounded_rectangle([x - 12, y + 14, x + wd + 12, y + size * 1.22], radius=20, fill=ACC)
                    d.text((x, y), w, font=f, fill=(20, 20, 30))
                else:
                    d.text((x, y), w, font=f, fill=(255, 255, 255), stroke_width=8, stroke_fill=(0, 0, 0))
            x += wd + space
            k += 1

def header(img, gt, total):
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([60, 70, W - 60, 88], radius=9, fill=(55, 50, 85))
    d.rounded_rectangle([60, 70, 60 + (W - 120) * min(1, gt / total), 88], radius=9, fill=ACC)
    d.text((W / 2, 150), "FIZZO FACTS", font=F(46), fill=(150, 230, 255), anchor="mm")

def cover_frame(base, gt, total):
    img = base.copy()
    header(img, gt, total)
    draw_fizzo(img, 290, 1270, 1.0, gt, "happy", 0, False)
    draw_gizmo(img, 800, 1300, 1.0, gt, "shock", 0, False)
    caption(img, None, cover_text(), 1, 0, size=120)
    return img

def envelope(a):
    n = int(len(a) / SR * FPS) + 1
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(a[i*hop:(i+1)*hop] ** 2)) if i*hop < len(a) else 0 for i in range(n)])
    env = env / (env.max() + 1e-6)
    return np.clip(env * 1.4, 0, 1)

def render(only=None):
    clips = list(np.load(OUT + "clips.npy", allow_pickle=True))
    durs = [len(c) / SR + GAP for c in clips]
    durs[0] += 0.15; durs[-1] += 0.8
    total = sum(durs) + COVER
    base = bg()
    flash_beats = FLASH
    offs = 0
    parts = []
    for bi, (spk, cap, ph, gm, fm) in enumerate(BEATS):
        n = int(round(durs[bi] * FPS))
        env = envelope(clips[bi])
        lead = 0.15 if bi == 0 else 0.0
        final, tmp = f"{OUT}beat{bi:02d}.mp4", f"{OUT}beat{bi:02d}.tmp.mp4"
        parts.append(final)
        if only is not None and bi not in only:
            offs += durs[bi]; continue
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                              "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
        talk = len(clips[bi]) / SR
        for k in range(n):
            t = k / FPS; gt = offs + t
            img = base.copy()
            if bi in flash_beats and t < 0.12:
                img = Image.blend(img, Image.new("RGB", (W, H), (255, 255, 255)), 0.5 * (1 - t / 0.12))
            header(img, gt, total)
            fi = int((t - lead) * FPS)
            m = env[fi] if 0 <= fi < len(env) else 0.0
            fz_act, gz_act = spk is FIZZO, spk is GIZMO
            draw_fizzo(img, 290, 1270, 0.95 * (1.06 if fz_act else 1), gt, fm, m if fz_act else 0, fz_act)
            draw_gizmo(img, 800, 1300, 0.95 * (1.06 if gz_act else 1), gt, gm, m if gz_act else 0, gz_act)
            caption(img, spk, cap, min(1, (t - lead + 0.15) / max(0.3, talk * 0.8)), t)
            if gm == "glitch" and spk is GIZMO and random.random() < 0.35:
                arr = np.array(img)
                y = random.randint(900, 1700); hgt = random.randint(20, 80)
                arr[y:y+hgt] = np.roll(arr[y:y+hgt], random.randint(-60, 60), axis=1)
                img = Image.fromarray(arr)
            p.stdin.write(img.tobytes())
        p.stdin.close()
        if p.wait() == 0:
            os.replace(tmp, final)
        offs += durs[bi]
    # end card: hook text, held still (also the cover frame)
    cov = f"{OUT}cover.mp4"; parts.append(cov)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                          "-pix_fmt", "yuv420p", cov], stdin=subprocess.PIPE)
    for k in range(int(round(COVER * FPS))):
        p.stdin.write(cover_frame(base, offs + k / FPS, total).tobytes())
    p.stdin.close(); p.wait()
    print("cover_ms", int((offs + COVER / 2) * 1000))
    # audio track
    track = np.zeros(int(total * SR) + SR, dtype=np.float32)
    start = 0.0
    for bi, c in enumerate(clips):
        i = int((start + (0.15 if bi == 0 else 0)) * SR)
        seg = c[: max(0, len(track) - i)]
        track[i:i + len(seg)] += seg
        start += durs[bi]
    track = track[: int(total * SR)]
    w = wave.open(OUT + "voice.wav", "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((np.clip(track / (np.abs(track).max() + 1e-6) * 0.9, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
    with open(OUT + "list.txt", "w") as fh:
        for x in parts:
            fh.write(f"file '{x}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", OUT + "list.txt",
                    "-i", OUT + "voice.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k",
                    "-af", "loudnorm=I=-14:TP=-1.5", "-ar", "44100", "-shortest", "-movflags", "+faststart",
                    OUT + "novoice_music.mp4"], check=True)
    mix_music(total)
    print("total", round(total, 2))

def mix_music(total):
    final = os.path.join(os.path.dirname(HERE), "videos", EP["id"] + ".mp4")
    subprocess.run([sys.executable, os.path.join(HERE, "beat.py"), str(round(total + 0.1, 2)), OUT + "beat.wav"], check=True)
    fc = ("[1:a]aresample=44100,aformat=channel_layouts=stereo,asplit=2[v][key];[2:a]volume=0.32[b];"
          "[b][key]sidechaincompress=threshold=0.03:ratio=6:attack=15:release=250[bd];"
          "[v][bd]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5[a]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", OUT + "novoice_music.mp4", "-i", OUT + "voice.wav",
                    "-i", OUT + "beat.wav", "-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", final], check=True)
    print("video", final)

def preview():
    clips = list(np.load(OUT + "clips.npy", allow_pickle=True))
    base = bg()
    shots = []
    n = len(BEATS)
    for bi in sorted({0, n // 3, (2 * n) // 3, n - 2}):
        spk, cap, ph, gm, fm = BEATS[bi]
        img = base.copy(); header(img, 10, 30)
        draw_fizzo(img, 290, 1270, 0.95 * (1.06 if spk is FIZZO else 1), 1.0, fm, 0.6 if spk is FIZZO else 0, spk is FIZZO)
        draw_gizmo(img, 800, 1300, 0.95 * (1.06 if spk is GIZMO else 1), 1.0, gm, 0.6 if spk is GIZMO else 0, spk is GIZMO)
        caption(img, spk, cap, 1, 1)
        shots.append(img.resize((360, 640)))
    shots.append(cover_frame(base, 1.0, 30).resize((360, 640)))
    sheet = Image.new("RGB", (360 * len(shots), 640))
    for i, im in enumerate(shots):
        sheet.paste(im, (i * 360, 0))
    sheet.save(OUT + "sheet.png"); print("preview", OUT + "sheet.png")

if __name__ == "__main__":
    cmd = sys.argv[2] if len(sys.argv) > 2 else "all"
    if cmd == "voices":
        for c in make_voices():
            print(round(len(c) / SR, 2))
    elif cmd == "preview":
        preview()
    elif cmd == "render":
        render()
    else:
        for c in make_voices():
            print(round(len(c) / SR, 2))
        preview()
        render()
