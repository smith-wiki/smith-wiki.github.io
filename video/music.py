"""Soundtrack of the smith.wiki announcement video (video/announce.html), synthesized from scratch.

Warm minimal electronica in F major at 113.2 BPM: one beat is 530 ms, the Klein cursor's blink,
so the cursor ticks land on the beat. Layers enter with the scenes (4.2, 11.6, 16.8, 22.2 s);
the call to action lands on a held Fmaj9 with three bell notes as the contacts appear.

    uv run --no-project --with numpy --with scipy python video/music.py OUT.wav
"""

import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt, sosfilt_zi

SR = 48_000
DURATION = 28.0
BEAT = 0.53
BAR = 4 * BEAT
SCENES = [0.0, 4.2, 11.6, 16.8, 22.2]
CTA = SCENES[4]
N = int(SR * DURATION)
t_all = np.arange(N) / SR
rng = np.random.default_rng(7)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def stereo(mono, pan=0.0):
    # Equal-power pan, -1 left .. 1 right.
    angle = (pan + 1) * np.pi / 4
    return np.stack([mono * np.cos(angle), mono * np.sin(angle)], axis=1)


def place(buf, sig, at):
    start = int(at * SR)
    if start >= len(buf):
        return
    end = min(len(buf), start + len(sig))
    buf[start:end] += sig[: end - start]


def env_adsr(n, attack, release, sustain_len):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    r = np.clip(1 - (t - sustain_len) / release, 0, 1)
    return a * r


def saw(freq, n, phase=0.0):
    t = np.arange(n) / SR
    return 2 * ((t * freq + phase) % 1.0) - 1


def swept_lowpass(sig, cutoff):
    # Two-pole Butterworth lowpass whose cutoff follows `cutoff` (Hz per sample), in 10 ms blocks.
    out = np.empty_like(sig)
    block = SR // 100
    zi = None
    for i in range(0, len(sig), block):
        fc = float(np.clip(cutoff[min(i, len(cutoff) - 1)], 40, SR * 0.45))
        sos = butter(2, fc, btype="low", fs=SR, output="sos")
        if zi is None:
            zi = sosfilt_zi(sos) * sig[0]
        out[i : i + block], zi = sosfilt(sos, sig[i : i + block], zi=zi)
    return out


def filt(sig, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=SR, output="sos"), sig)


# F major: Fmaj9, Am7, Dm9, Bbmaj7(#11); one chord per bar. The CTA holds Fmaj9.
CHORDS = [
    ([53, 57, 60, 64, 67], 41),
    ([57, 60, 64, 67], 45),
    ([50, 53, 57, 60, 64], 38),
    ([46, 50, 53, 57, 64], 34),
]
FMAJ9 = ([53, 57, 60, 64, 67, 72], 41)


def chord_at(time):
    if time >= CTA:
        return FMAJ9
    return CHORDS[int(time // BAR) % len(CHORDS)]


kick_times = [i * BEAT for i in range(int(DURATION / BEAT) + 1)]
drums_on = lambda time: SCENES[1] <= time < CTA - 0.02  # noqa: E731

# ---- pad: detuned saws per chord, filter opening scene by scene ----
pad = np.zeros(N)
bar_starts = [i * BAR for i in range(int(CTA // BAR) + 1)] + [CTA]
bar_starts = sorted(set(round(b, 4) for b in bar_starts if b <= CTA))
segments = [(s, e) for s, e in zip(bar_starts, bar_starts[1:] + [DURATION])]
for start, end in segments:
    notes, _ = chord_at(start + 1e-3)
    length = end - start
    n = int((length + 1.2) * SR)
    env = env_adsr(n, 0.35 if start > 0 else 1.2, 1.2, length)
    voice = np.zeros(n)
    for note in notes:
        for cents in (-8, 0, 8):
            voice += saw(hz(note) * 2 ** (cents / 1200), n, rng.random())
    place(pad, voice * env / (len(notes) * 3), start)
cutoff = np.interp(
    t_all,
    [0, 4.2, 11.6, 16.8, 21.6, 22.2, 25.0, 28.0],
    [500, 900, 1500, 2300, 3200, 1400, 2600, 1200],
)
pad = swept_lowpass(pad, cutoff) * 0.55 * np.interp(t_all, [0, 4.2, 4.3, 22.2, 22.4, 28], [1.8, 1.8, 1.0, 1.0, 1.5, 1.5])

# ---- sub bass: root in eighths from scene 2, long root under the CTA ----
bass = np.zeros(N)
for i in range(int(DURATION / (BEAT / 2))):
    at = i * BEAT / 2
    if not (SCENES[1] <= at < CTA):
        continue
    _, root = chord_at(at)
    n = int(BEAT / 2 * SR)
    t = np.arange(n) / SR
    tone = np.sin(2 * np.pi * hz(root) * t) + 0.25 * np.sin(4 * np.pi * hz(root) * t)
    place(bass, np.tanh(1.6 * tone) * np.exp(-t * 5) * 0.36, at)
n = int((DURATION - CTA) * SR)
t = np.arange(n) / SR
place(bass, np.sin(2 * np.pi * hz(41) * t) * np.exp(-t * 0.45) * 0.3, CTA)

# ---- plucks: arpeggio over the chord; eighths, then sixteenths from scene 3 ----
plucks_l = np.zeros((N, 2))
step = 0
at = 0.0
while at < CTA - 0.01:
    notes, _ = chord_at(at)
    if at >= SCENES[1] or step % 2 == 0:
        note = notes[[0, 2, 4, 1, 3, 2, 4, 3][step % 8] % len(notes)] + 12
        n = int(0.6 * SR)
        t = np.arange(n) / SR
        f = hz(note)
        tone = (np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 18))) * np.exp(-t * 7)
        level = 0.16 if at < SCENES[2] else 0.13
        side = step % 2 if at >= SCENES[1] else (step // 2) % 2
        place(plucks_l, stereo(tone * level, 0.45 if side else -0.45), at)
    step += 1
    at += BEAT / 2 if at < SCENES[2] else BEAT / 4

# ---- drums ----
drums = np.zeros(N)
for at in kick_times:
    if not drums_on(at):
        continue
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    freq = 48 + 70 * np.exp(-t * 28)
    kick = np.sin(2 * np.pi * np.cumsum(freq) / SR) * np.exp(-t * 9)
    place(drums, kick * 0.72, at)
    hat_n = int(0.05 * SR)
    hat = filt(rng.standard_normal(hat_n), "high", 7000) * np.exp(-np.arange(hat_n) / SR * 90)
    place(drums, hat * 0.18, at + BEAT / 2)
    beat_index = round(at / BEAT)
    if at >= SCENES[2] and beat_index % 2 == 1:
        clap_n = int(0.18 * SR)
        noise = filt(rng.standard_normal(clap_n), "band", [900, 2600])
        tc = np.arange(clap_n) / SR
        bursts = sum(np.exp(-np.clip(tc - d, 0, None) * 60) * (tc >= d) for d in (0, 0.012, 0.024))
        place(drums, noise * bursts * 0.16, at)
    if at >= SCENES[3]:
        place(drums, hat * 0.09, at + BEAT / 4)
        place(drums, hat * 0.09, at + 3 * BEAT / 4)

# Sidechain: pad and bass duck under each kick.
duck = np.ones(N)
for at in kick_times:
    if drums_on(at):
        i = int(at * SR)
        n = min(N - i, int(0.3 * SR))
        duck[i : i + n] = np.minimum(duck[i : i + n], 1 - 0.45 * np.exp(-np.arange(n) / SR * 11))

# ---- scene accents: swells into each change, a low boom on it, a reverse swell into the CTA ----
fx = np.zeros(N)
for change in SCENES[1:]:
    length = 1.0 if change == CTA else 0.6
    n = int(length * SR)
    rise = np.linspace(0, 1, n) ** 3
    swell = filt(rng.standard_normal(n), "band", [1500, 6000]) * rise * (0.10 if change == CTA else 0.06)
    place(fx, swell, change - length)
    bn = int(1.4 * SR)
    tb = np.arange(bn) / SR
    boom = np.sin(2 * np.pi * (38 + 30 * np.exp(-tb * 12)) * tb) * np.exp(-tb * 3.2)
    place(fx, boom * (0.35 if change == CTA else 0.2), change)

# ---- the cursor: a soft tick on every blink while the Klein block is on screen ----
ticks = np.zeros(N)
tick_n = int(0.03 * SR)
tt = np.arange(tick_n) / SR
tick = np.sin(2 * np.pi * 2400 * tt) * np.exp(-tt * 160)
for k in range(int(DURATION / BEAT) + 1):
    at = k * BEAT
    if at < SCENES[1] - 0.1 or at >= CTA + 0.53:
        place(ticks, tick * (0.05 if k % 2 == 0 else 0.03), at)

# ---- bells: C5 E5 G5 as email, X, and web appear in the CTA ----
bells = np.zeros((N, 2))
for at, note, pan in ((23.6, 72, -0.3), (23.9, 76, 0.0), (24.2, 79, 0.3)):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = hz(note)
    bell = (np.sin(2 * np.pi * f * t + 1.4 * np.sin(2 * np.pi * 3.5 * f * t) * np.exp(-t * 4)) * np.exp(-t * 1.6))
    place(bells, stereo(bell * 0.12, pan), at)

# ---- mix ----
dry = stereo(pad * duck, 0) + stereo(bass * duck, 0) + plucks_l + stereo(drums, 0) + stereo(fx, 0) + stereo(ticks, 0) + bells
send = stereo(pad * duck * 0.5, 0) + plucks_l * 0.8 + bells * 0.9 + stereo(fx * 0.3, 0)

ir_n = int(2.4 * SR)
ir_t = np.arange(ir_n) / SR
ir = np.stack([rng.standard_normal(ir_n), rng.standard_normal(ir_n)], axis=1) * np.exp(-ir_t * 2.6)[:, None]
ir = np.stack([filt(ir[:, c], "low", 6000) for c in range(2)], axis=1)
ir /= np.sqrt((ir**2).sum(axis=0))
wet = np.stack([fftconvolve(send[:, c], ir[:, c])[:N] for c in range(2)], axis=1)

mix = dry + 0.35 * wet
mix[:, 0] = filt(mix[:, 0], "high", 38)
mix[:, 1] = filt(mix[:, 1], "high", 38)
fade_in = np.clip(t_all / 0.08, 0, 1)
fade_out = np.clip((DURATION - t_all) / 2.2, 0, 1) ** 1.5
mix *= (fade_in * fade_out)[:, None]
mix = np.tanh(mix / np.abs(mix).max() * 1.4) * 0.89

wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print(f"wrote {sys.argv[1]}: {DURATION}s, {SR} Hz stereo")
