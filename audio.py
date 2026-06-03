"""
PLANZARA — Audio Manager
Procedural music & SFX synthesis using pygame.mixer.
Zero external audio files required.
"""
import pygame, math, array, random

_SR = 22050   # sample rate


def _stereo16(samples):
    """Pack mono int16 list → stereo array.array('h')."""
    buf = array.array('h')
    for s in samples:
        buf.append(s); buf.append(s)
    return buf


def _tone(freq, dur, vol=0.18, atk=0.02, rel=0.05, cache={}):
    key = (round(freq, 1), round(dur, 3), round(vol, 3))
    if key in cache:
        return cache[key]
    n = int(_SR * dur)
    a = max(1, int(_SR * atk))
    r = max(1, int(_SR * rel))
    pf = 2.0 * math.pi * freq / _SR
    smp = []
    for i in range(n):
        v = vol * math.sin(pf * i)
        if i < a:   v *= i / a
        elif i > n - r: v *= (n - i) / r
        smp.append(max(-32767, min(32767, int(v * 32767))))
    snd = pygame.mixer.Sound(buffer=_stereo16(smp))
    cache[key] = snd
    return snd


def _glide(f0, f1, dur, vol=0.20, cache={}):
    key = ('gl', round(f0), round(f1), round(dur, 3))
    if key in cache:
        return cache[key]
    n = int(_SR * dur)
    a = max(1, int(_SR * 0.01)); r = max(1, int(_SR * 0.03))
    phase = 0.0; smp = []
    for i in range(n):
        phase += 2 * math.pi * (f0 + (f1 - f0) * i / n) / _SR
        v = vol * math.sin(phase)
        if i < a: v *= i / a
        elif i > n - r: v *= (n - i) / r
        smp.append(max(-32767, min(32767, int(v * 32767))))
    snd = pygame.mixer.Sound(buffer=_stereo16(smp))
    cache[key] = snd
    return snd


def _noise(dur, vol=0.14, cache={}):
    key = ('nx', round(dur, 3))
    if key in cache:
        return cache[key]
    n = int(_SR * dur); f = max(1, n // 8); smp = []
    for i in range(n):
        v = vol * (random.random() * 2 - 1)
        if i < f: v *= i / f
        elif i > n - f: v *= (n - i) / f
        smp.append(max(-32767, min(32767, int(v * 32767))))
    snd = pygame.mixer.Sound(buffer=_stereo16(smp))
    cache[key] = snd
    return snd


def _bgm_buf(schedule, total, mvol=0.13):
    """Build a complete loop buffer from a note schedule list.
       schedule: [(t0, freq, dur), ...] or [(t0, freq, dur, vol), ...]
    """
    N = int(_SR * total)
    buf = [0.0] * N
    for note in schedule:
        t0, freq, dur = note[0], note[1], note[2]
        v = note[3] if len(note) > 3 else mvol
        i0 = int(t0 * _SR)
        ni = int(dur * _SR)
        rel = max(1, min(int(_SR * 0.04), ni // 4))
        atk = max(1, min(int(_SR * 0.02), ni // 6))
        pf = 2.0 * math.pi * freq / _SR
        for i in range(min(ni, N - i0)):
            amp = v * (i / atk if i < atk else ((ni - i) / rel if i > ni - rel else 1.0))
            buf[i0 + i] += amp * math.sin(pf * i)
    mx = max((abs(x) for x in buf), default=1.0)
    sc = 0.92 / mx if mx > 0.92 else 1.0
    smp = [max(-32767, min(32767, int(x * sc * 32767))) for x in buf]
    return pygame.mixer.Sound(buffer=_stereo16(smp))


# ═══════════════════════════════════════════════════════════════════════
class AudioManager:
    """Central audio controller. Call play_bgm(name) and play_sfx(name)."""

    def __init__(self):
        self._ok = False
        try:
            pygame.mixer.pre_init(_SR, -16, 2, 512)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self._ok = True
        except Exception:
            return

        self._bgm_ch   = pygame.mixer.Channel(0)
        self._bgm_name = None
        self._sfx_chs  = [pygame.mixer.Channel(i) for i in range(1, 8)]
        self._sfx_ci   = 0

        self.sfx    = {}
        self.tracks = {}
        self._build_sfx()
        self._build_tracks()

    # ── SFX ────────────────────────────────────────────────────────────
    def _build_sfx(self):
        S = self.sfx
        S['blip']     = _tone(880,  0.04, 0.09)
        S['select']   = _tone(659,  0.10, 0.16)
        S['confirm']  = _tone(784,  0.16, 0.18)
        S['cancel']   = _glide(440, 330, 0.14, 0.16)
        S['portal']   = _glide(220, 880, 0.70, 0.22)
        S['glitch']   = _noise(0.12, 0.22)
        S['alert']    = _glide(660, 220, 0.35, 0.20)
        S['notify']   = _tone(1047, 0.18, 0.14)
        S['click']    = _tone(1200, 0.03, 0.11)
        S['power']    = _glide(110, 440, 0.40, 0.18)
        S['rain']     = _noise(0.10, 0.05)
        S['whoosh']   = _glide(800, 200, 0.25, 0.16)
        S['phone']    = _tone(660,  0.30, 0.20)

    # ── BGM tracks (looping buffers) ───────────────────────────────────
    def _build_tracks(self):
        T = self.tracks

        # TITLE — 4 s atmospheric
        T['title'] = _bgm_buf([
            (0.0, 110, 4.0, 0.08), (0.0, 220, 1.1, 0.12),
            (1.1, 165, 0.9, 0.10), (2.0, 208, 0.9, 0.11),
            (2.9, 220, 0.9, 0.12), (3.8, 247, 0.3, 0.10),
            (0.5, 440, 0.14, 0.07),(1.6, 660, 0.12, 0.06),
            (2.8, 554, 0.16, 0.07),(0.0, 165, 2.0, 0.07),
            (2.0, 175, 2.0, 0.07),(0.0,  55, 4.0, 0.05),
        ], 4.0)

        # APARTMENT — 2 s upbeat
        T['apartment'] = _bgm_buf([
            (0.0, 110, 2.0, 0.07),(0.0, 262, 0.4, 0.12),
            (0.4, 330, 0.3, 0.11),(0.7, 392, 0.3, 0.12),
            (1.0, 330, 0.3, 0.10),(1.3, 262, 0.3, 0.11),
            (1.6, 220, 0.2, 0.10),(0.0, 392, 0.14, 0.07),
            (0.5, 523, 0.12, 0.07),(1.0, 494, 0.12, 0.06),
            (1.5, 440, 0.12, 0.06),
        ], 2.0)

        # LAB — 3 s tense-mysterious
        T['lab'] = _bgm_buf([
            (0.0, 110, 3.0, 0.09),(0.0, 165, 0.7, 0.11),
            (0.7, 196, 0.5, 0.10),(1.2, 208, 0.5, 0.11),
            (1.7, 220, 0.5, 0.12),(2.2, 208, 0.4, 0.10),
            (2.6, 196, 0.5, 0.10),(0.3, 233, 0.24, 0.05),
            (1.5, 247, 0.20, 0.05),(2.5, 233, 0.20, 0.05),
            (0.0,  55, 3.0, 0.06),
        ], 3.0)

        # TRAVEL — 1.5 s fast/intense
        T['travel'] = _bgm_buf([
            (0.0,  110, 1.5, 0.08),
            (0.00, 262, 0.12, 0.10),(0.12, 294, 0.12, 0.10),
            (0.24, 330, 0.12, 0.10),(0.36, 370, 0.12, 0.11),
            (0.48, 392, 0.12, 0.11),(0.60, 440, 0.12, 0.12),
            (0.72, 494, 0.12, 0.12),(0.84, 523, 0.12, 0.13),
            (0.96, 587, 0.12, 0.13),(1.08, 659, 0.12, 0.14),
            (1.20, 784, 0.30, 0.14),
            (0.30,1047, 0.10, 0.06),(0.90,1175, 0.10, 0.06),
        ], 1.5)

        # SCHOOL 2026 — 2.5 s slightly tense
        T['school'] = _bgm_buf([
            (0.0, 73, 2.5, 0.08),(0.0, 147, 0.6, 0.11),
            (0.6, 175, 0.4, 0.10),(1.0, 165, 0.5, 0.11),
            (1.5, 147, 0.5, 0.10),(2.0, 131, 0.6, 0.11),
            (0.8, 294, 0.20, 0.06),(1.8, 262, 0.20, 0.06),
        ], 2.5)

        # TEA SHOP — 2 s relaxed-rainy
        T['tea'] = _bgm_buf([
            (0.0,  98, 2.0, 0.08),(0.0, 196, 0.5, 0.11),
            (0.5, 247, 0.4, 0.10),(0.9, 294, 0.4, 0.11),
            (1.3, 247, 0.4, 0.10),(1.7, 220, 0.3, 0.10),
            (0.25,392, 0.14, 0.06),(0.75,440, 0.12, 0.06),
            (1.25,494, 0.12, 0.06),(1.75,440, 0.12, 0.06),
        ], 2.0)

        # SCOOTY RIDE — 1.5 s energetic synthwave
        T['scooty'] = _bgm_buf([
            (0.0, 110, 1.5, 0.08),
            (0.0, 330, 0.20, 0.12),(0.2, 392, 0.20, 0.12),
            (0.4, 440, 0.20, 0.13),(0.6, 494, 0.20, 0.13),
            (0.8, 523, 0.20, 0.14),(1.0, 587, 0.20, 0.14),
            (1.2, 659, 0.30, 0.14),
            (0.0, 660, 0.10, 0.08),(0.5, 880, 0.10, 0.08),
            (1.0, 990, 0.10, 0.08),
        ], 1.5)

        # CHAPTER END — 4 s emotional-epic
        T['end'] = _bgm_buf([
            (0.0, 110, 4.0, 0.09),(0.0, 220, 1.0, 0.12),
            (1.0, 277, 0.8, 0.11),(1.8, 330, 1.0, 0.12),
            (2.8, 277, 0.7, 0.11),(3.5, 220, 0.5, 0.12),
            (0.0, 440, 0.18, 0.07),(0.5, 523, 0.15, 0.07),
            (1.0, 587, 0.15, 0.07),(1.5, 659, 0.15, 0.07),
            (2.0, 784, 0.20, 0.08),(2.5, 659, 0.15, 0.07),
            (3.0, 587, 0.15, 0.07),(3.5, 523, 0.20, 0.07),
        ], 4.0)

        # CLIFFHANGER — 3 s dramatic
        T['cliff'] = _bgm_buf([
            (0.0,  82, 3.0, 0.09),(0.0, 165, 0.8, 0.10),
            (0.8, 175, 0.5, 0.09),(1.3, 165, 0.5, 0.10),
            (1.8, 155, 0.6, 0.09),(2.4, 139, 0.7, 0.10),
            (0.5, 330, 0.20, 0.06),(1.5, 349, 0.20, 0.05),
            (2.5, 311, 0.20, 0.06),
        ], 3.0)

        # PHONE CALL — simple ringtone loop 1.2 s
        T['phone'] = _bgm_buf([
            (0.0, 660, 0.3, 0.18),(0.35, 880, 0.3, 0.18),
        ], 1.2)

    # ── public API ──────────────────────────────────────────────────────
    def play_sfx(self, name):
        if not self._ok: return
        snd = self.sfx.get(name)
        if snd:
            ch = self._sfx_chs[self._sfx_ci % len(self._sfx_chs)]
            self._sfx_ci += 1
            ch.play(snd)

    def play_bgm(self, name):
        if not self._ok or name == self._bgm_name: return
        self._bgm_name = name
        self._bgm_ch.stop()
        snd = self.tracks.get(name)
        if snd:
            self._bgm_ch.play(snd, loops=-1)

    def stop_bgm(self, fade=400):
        if not self._ok: return
        self._bgm_ch.fadeout(fade)
        self._bgm_name = None

    def set_bgm_volume(self, v):
        if self._ok: self._bgm_ch.set_volume(max(0.0, min(1.0, v)))

    def update(self):
        pass   # BGM runs via loops=-1 automatically