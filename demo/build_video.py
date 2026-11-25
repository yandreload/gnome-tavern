#!/usr/bin/env python3
"""Build the Gnome Tavern demo video (1280x720, ~60s).

Scenes (all visuals are the REAL working app / REAL tx logs):
 1. Title card (PIL)
 2. gnoweb tavern page screenshot, slow vertical scroll (real Render output)
 3. Terminal card with the real Faucet tx log
 4. Terminal card with the real BuyDrink tx log
 5. gnoweb tab page screenshot (real on-chain tab) + closing card
Narration: Aria TTS (English), one segment per scene.
"""
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path("/home/hatch/workspace/gnome-tavern")
DEMO = BASE / "demo"
W, H = 1280, 720

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

TTS = "/opt/hatch/bin/tts"
VOICE = "avocado_v2:MAI_01"

SCENES = [
    {
        "id": "title",
        "kind": "title",
        "narr": "Welcome to the Gnome Tavern — an on-chain tavern on Gno.land, built for the Gnome Tavern hackathon.",
    },
    {
        "id": "tavern",
        "kind": "scroll",
        "img": DEMO / "shot-tavern-full.png",
        "narr": "The tavern is a Gno realm. It mints its own token, Tavern Ale, serves five drinks, and keeps every patron's tab on-chain, forever.",
    },
    {
        "id": "faucet",
        "kind": "terminal",
        "log": DEMO / "tx-faucet.txt",
        "title": "1 · Claim free Ale — Faucet()",
        "narr": "Anyone can claim one hundred Ale from the faucet, once every twenty-four hours. Here is the real transaction: one hundred Ale minted to a brand new patron.",
    },
    {
        "id": "buy",
        "kind": "terminal",
        "log": DEMO / "tx-buydrink.txt",
        "title": "2 · Buy a drink — BuyDrink(\"Gnome Stout\")",
        "narr": "Then the patron buys a Gnome Stout for fifty Ale. The payment goes straight to the tavern till, and the drink lands on their tab.",
    },
    {
        "id": "tab",
        "kind": "image",
        "img": DEMO / "shot-tab.png",
        "narr": "The tab page shows it live, and the leaderboard ranks the top patrons. The code, tests, and deployment guide are in the repository. Cheers — see you at the tavern.",
    },
]


def run(cmd, **kw):
    print("+", " ".join(str(c) for c in cmd[:6]), "...")
    subprocess.run(cmd, check=True, **kw)


def tts(text: str, out: Path):
    run([TTS, "speak", "--output", str(out), "--voice", VOICE,
         "--language", "en", "--text-stdin"],
        input=text.encode())


def duration(path: Path) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", str(path)],
        capture_output=True, text=True, check=True).stdout
    return float(json.loads(out)["format"]["duration"])


def title_card() -> Path:
    img = Image.new("RGB", (W, H), (15, 46, 29))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 90], fill=(21, 94, 61))
    d.rectangle([0, H - 70, W, H], fill=(21, 94, 61))
    f_big = ImageFont.truetype(SANS_B, 92)
    f_sub = ImageFont.truetype(SANS, 34)
    f_small = ImageFont.truetype(SANS, 26)
    d.text((80, 190), "Gnome Tavern", font=f_big, fill=(255, 255, 255))
    d.text((82, 300), "An on-chain tavern on Gno.land", font=f_sub, fill=(220, 240, 228))
    d.text((82, 350), "GRC20 Tavern Ale  ·  rate-limited faucet  ·  drink tabs on-chain",
           font=f_small, fill=(180, 210, 192))
    d.text((82, H - 52), "Gnome Tavern Hackathon  •  Gno.land testnet (Onyx)  •  yandreload/gnome-tavern",
           font=ImageFont.truetype(SANS, 22), fill=(220, 240, 228))
    p = DEMO / "frame-title.png"
    img.save(p)
    return p


def terminal_card(log: Path, title: str) -> Path:
    # Faithful excerpt of the real tx log: command, return value, receipt.
    # The giant EVENTS JSON blob is shown truncated, values untouched.
    lines = []
    raw = log.read_text().splitlines()
    for ln in raw:
        if ln.startswith("EVENTS:"):
            lines.append("EVENTS:     [{\"type\":\"Transfer\", ...}]  (full log in repo/demo/)")
            continue
        if ln.startswith("INFO:"):
            continue
        lines.append(ln)
    img = Image.new("RGB", (W, H), (13, 17, 23))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 56], fill=(22, 27, 34))
    d.text((28, 14), title, font=ImageFont.truetype(MONO_B, 26), fill=(125, 211, 252))
    f = ImageFont.truetype(MONO, 20)
    fb = ImageFont.truetype(MONO_B, 20)
    y = 78
    for ln in lines:
        # wrap long lines at 92 cols
        while len(ln) > 92:
            chunk, ln = ln[:92], ln[92:]
            d.text((28, y), chunk, font=f, fill=(230, 237, 243))
            y += 28
        if not ln:
            y += 14
            continue
        col = (230, 237, 243)
        font = f
        if ln.startswith("$ "):
            col, font = (126, 231, 135), fb
        elif ln.startswith("OK!") or "int64" in ln or "string" in ln:
            col, font = (126, 231, 135), fb
        elif ln.startswith("TX HASH:"):
            col = (255, 214, 102)
        d.text((28, y), ln, font=font, fill=col)
        y += 28
        if y > H - 40:
            break
    p = DEMO / f"frame-{log.stem}.png"
    img.save(p)
    return p


def prep_image(src: Path) -> Path:
    im = Image.open(src).convert("RGB")
    if im.size[1] < H:  # letterbox short screenshots
        out = Image.new("RGB", (W, H), (255, 255, 255))
        out.paste(im, (0, (H - im.size[1]) // 2))
        im = out
    p = DEMO / f"frame-{src.stem}.png"
    im.save(p)
    return p


def main():
    # 1. narration per scene
    audio = []
    for sc in SCENES:
        a = DEMO / f"narr-{sc['id']}.mp3"
        if not a.exists():
            tts(sc["narr"], a)
        dur = duration(a)
        sc["dur"] = dur + 0.9  # breathing room
        audio.append(a)
        print(sc["id"], "audio", round(dur, 2), "s -> scene", round(sc["dur"], 2), "s")

    # 2. visuals
    frames = {}
    frames["title"] = title_card()
    for sc in SCENES:
        if sc["kind"] == "terminal":
            frames[sc["id"]] = terminal_card(sc["log"], sc["title"])
        elif sc["kind"] in ("image", "scroll"):
            frames[sc["id"]] = prep_image(sc["img"])

    # 3. build each scene clip, then concat
    clips = []
    for i, sc in enumerate(SCENES):
        out = DEMO / f"clip-{i}-{sc['id']}.mp4"
        img = frames[sc["id"]]
        dur = sc["dur"]
        if sc["kind"] == "scroll":
            # slow vertical scroll over the 1280x1250 screenshot (y 60 -> 530)
            vf = (f"crop=1280:720:0:'60+470*min(t/{dur:.2f}\\,1)',setsar=1,"
                  f"scale=1280:720")
            filt = f"[0:v]{vf}[v]"
        else:
            filt = "[0:v]scale=1280:720,setsar=1[v]"
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-i", str(img),
             "-i", str(audio[i]), "-filter_complex", filt,
             "-map", "[v]", "-map", "1:a", "-t", f"{dur:.2f}",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
             "-c:a", "aac", "-b:a", "128k", "-shortest", str(out)])
        clips.append(out)

    lst = DEMO / "concat.txt"
    lst.write_text("".join(f"file '{c}'\n" for c in clips))
    final = BASE / "demo" / "gnome-tavern-demo.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
         "-i", str(lst), "-c", "copy", str(final)])
    print("TOTAL", round(sum(s["dur"] for s in SCENES), 1), "s ->", final,
          final.stat().st_size, "bytes")
    subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                    "format=duration,size", "-of", "default=noprint_wrappers=1",
                    str(final)], check=False)


if __name__ == "__main__":
    main()
