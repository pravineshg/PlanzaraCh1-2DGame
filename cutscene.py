"""
PLANZARA — cutscene.py
Cinematic cutscene sequences: intro, time-travel, cliffhanger, chapter-end.
Each cutscene is a self-contained object: update(dt), draw(surf), done property.
"""
import pygame, math, random
import sprites

W, H = 960, 540


# ══════════════════════════════════════════════════════════════════════
# Shared helpers
# ══════════════════════════════════════════════════════════════════════

def _lerp(a, b, t): return a + (b - a) * t

def _ease_in_out(t): return t * t * (3 - 2 * t)

def _text_fade(surf, font, text, x, y, alpha, color=(200, 220, 255), center=False):
    ts = font.render(text, True, color)
    ts.set_alpha(max(0, min(255, int(alpha))))
    bx = x - ts.get_width()//2 if center else x
    surf.blit(ts, (bx, y))
    return ts.get_width(), ts.get_height()

def _blue_particles(surf, particles, t):
    for p in particles:
        a = int(200 * (p['life'] / p['max']))
        r = max(1, p.get('r', 2))
        ps = pygame.Surface((r*2+2, r*2+2), pygame.SRCALPHA)
        pygame.draw.circle(ps, (p['c'][0], p['c'][1], p['c'][2], a), (r+1, r+1), r)
        surf.blit(ps, (int(p['x']-r-1), int(p['y']-r-1)),
                  special_flags=pygame.BLEND_RGBA_ADD)

def _spawn_blue_particles(particles, count=3):
    for _ in range(count):
        col = random.choice([(0,180,255),(0,220,200),(80,160,255),(0,255,220)])
        particles.append({
            'x': random.uniform(0, W), 'y': random.uniform(0, H),
            'vx': random.uniform(-20, 20), 'vy': random.uniform(-40, -10),
            'life': random.uniform(2.0, 5.0), 'max': 5.0,
            'r': random.randint(1, 3), 'c': col,
        })

def _update_particles(particles, dt):
    alive = []
    for p in particles:
        p['x'] += p['vx'] * dt
        p['y'] += p['vy'] * dt
        p['life'] -= dt
        if p['life'] > 0:
            alive.append(p)
    particles[:] = alive


# ══════════════════════════════════════════════════════════════════════
# Base
# ══════════════════════════════════════════════════════════════════════

class CutsceneBase:
    def __init__(self, fonts):
        self.f_xl, self.f_lg, self.f_md, self.f_sm, self.f_xs = fonts
        self._done = False
        self._t    = 0.0

    @property
    def done(self): return self._done

    def skip(self): self._done = True

    def update(self, dt):
        self._t += dt

    def draw(self, surf):
        pass

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE,
                             pygame.K_z, pygame.K_e):
                self.skip()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.skip()


# ══════════════════════════════════════════════════════════════════════
# 1. OPENING CINEMATIC  (dark silhouette, particles, text crawl)
# ══════════════════════════════════════════════════════════════════════

_INTRO_LINES = [
    "Humanity once feared time.",
    "The future was uncertain.",
    "Then the timelines were connected.",
    "And civilization evolved beyond imagination.",
]

_INTRO_PHASES = [
    # (start_t, end_t, label)
    (0.0,  3.0,  'black'),
    (3.0,  9.0,  'particles'),
    (9.0,  18.0, 'text'),
    (18.0, 26.0, 'silhouette'),
    (26.0, 32.0, 'city'),
    (32.0, 36.0, 'fadeout'),
]

class IntroCinematic(CutsceneBase):
    def __init__(self, fonts):
        super().__init__(fonts)
        self._particles = []
        self._stars     = [(random.uniform(0,W), random.uniform(0,H),
                            random.uniform(0.3,1.5)) for _ in range(180)]
        self._silhouette_surf = self._build_silhouette()
        self._city_surf       = self._build_city()
        self._fade_alpha = 255.0
        self._text_alpha = [0.0] * len(_INTRO_LINES)

    def _build_silhouette(self):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        bs = 6
        from sprites import draw_char, SILHOUETTE, CW, CH
        ox = W//2 - CW*bs//2
        oy = H//2 - CH*bs//2
        draw_char(s, SILHOUETTE, ox, oy, bs)
        # Eye glows
        for ex, ey in [(ox + 3*bs + bs//2, oy + 3*bs + bs//2),
                       (ox + 7*bs + bs//2, oy + 3*bs + bs//2)]:
            g = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(g, (100, 210, 255, 200), (15, 15), 14)
            pygame.draw.circle(g, (200, 240, 255, 240), (15, 15), 6)
            s.blit(g, (ex-15, ey-15), special_flags=pygame.BLEND_RGBA_ADD)
        return s

    def _build_city(self):
        s = pygame.Surface((W, H))
        # Night sky gradient
        for i in range(H):
            c = int(4 + i/H * 18)
            pygame.draw.line(s, (c//2, c//2, c*3), (0, i), (W, i))
        # Skyline
        bldgs = [(0,180,120,360),(130,140,80,400),(220,200,100,340),
                 (340,160,90,380),(450,120,110,420),(580,180,80,360),
                 (680,140,100,400),(800,160,90,380),(910,120,110,420),(1040,180,80,360)]
        for bx, _, bw, bh in bldgs:
            by = H - bh
            pygame.draw.rect(s, (8, 12, 40), (bx, by, bw, bh))
            for wy in range(by+8, H-8, 14):
                for wx in range(bx+8, bx+bw-8, 10):
                    if random.random() > 0.4:
                        col = random.choice([(0,180,255),(0,255,200),(255,200,0)])
                        pygame.draw.rect(s, col, (wx, wy, 5, 8))
        return s

    def update(self, dt):
        super().update(dt)
        _spawn_blue_particles(self._particles, 2)
        _update_particles(self._particles, dt)
        # Fade in from black
        if self._fade_alpha > 0 and self._t > 1.0:
            self._fade_alpha = max(0, self._fade_alpha - dt*180)
        # Text lines
        for i, line in enumerate(_INTRO_LINES):
            start = 9.0 + i * 2.2
            end   = start + 2.0
            if self._t >= start:
                self._text_alpha[i] = min(255, self._text_alpha[i] + dt*200)
            elif self._t > end + 1.5:
                self._text_alpha[i] = max(0, self._text_alpha[i] - dt*100)
        # Auto-end
        if self._t > 36.0:
            self._done = True

    def draw(self, surf):
        surf.fill((0, 0, 0))
        t = self._t

        # Stars
        for sx, sy, br in self._stars:
            a = int(br * (100 + math.sin(t * br + sx) * 30))
            s = pygame.Surface((3, 3), pygame.SRCALPHA)
            pygame.draw.circle(s, (200, 220, 255, min(255,a)), (1,1), 1)
            surf.blit(s, (int(sx), int(sy)))

        # Particles
        _blue_particles(surf, self._particles, t)

        # Text phase
        if 9.0 <= t <= 22.0:
            for i, line in enumerate(_INTRO_LINES):
                a = self._text_alpha[i]
                if a > 2:
                    _text_fade(surf, self.f_md, line, W//2, 180 + i*55,
                               a, (180, 210, 255), center=True)

        # Silhouette
        if 18.0 <= t <= 30.0:
            p = min(1.0, (t - 18.0) / 3.0)
            self._silhouette_surf.set_alpha(int(_ease_in_out(p) * 200))
            surf.blit(self._silhouette_surf, (0, 0))

        # City reveal
        if 26.0 <= t <= 36.0:
            p = min(1.0, (t - 26.0) / 4.0)
            self._city_surf.set_alpha(int(_ease_in_out(p) * 240))
            surf.blit(self._city_surf, (0, 0))

        # Fade-in from black
        if self._fade_alpha > 0:
            fb = pygame.Surface((W, H))
            fb.fill((0, 0, 0))
            fb.set_alpha(int(self._fade_alpha))
            surf.blit(fb, (0, 0))

        # Skip hint
        if t > 2.0 and t < 34.0:
            _text_fade(surf, self.f_xs, "PRESS ANY KEY TO SKIP",
                       W - 230, H - 26, min(150, (t-2)*50), (70, 90, 130))


# ══════════════════════════════════════════════════════════════════════
# 2. TITLE SCREEN (animated, not a cutscene per se but shares interface)
# ══════════════════════════════════════════════════════════════════════

class TitleScreen(CutsceneBase):
    def __init__(self, fonts):
        super().__init__(fonts)
        self._particles   = []
        self._city_scroll = 0.0
        self._title_alpha = 0.0
        self._sub_alpha   = 0.0
        self._press_alpha = 0.0
        self._bg  = self._build_bg()
        self._stars = [(random.uniform(0,W), random.uniform(0,H),
                        random.uniform(0.4,1.2)) for _ in range(120)]
        self._vehicles = [
            {'x': random.uniform(0, W*2), 'y': random.uniform(220, 340),
             'speed': random.uniform(80, 200), 'color': random.choice(
                [(0,200,255),(255,100,80),(200,255,100)]),
             'w': random.randint(50, 80)}
            for _ in range(12)
        ]

    def _build_bg(self):
        s = pygame.Surface((W*2, H))
        for i in range(H):
            c = int(4 + i/H*18)
            pygame.draw.line(s, (c//3, c//3, c*3), (0, i), (W*2, i))
        bldgs = [(0,50,120,340),(130,80,90,310),(230,40,140,360),
                 (390,70,100,330),(510,50,120,350),(650,80,90,320),
                 (760,40,130,360),(910,60,100,340),(1040,80,110,310),
                 (1170,50,120,340),(1310,70,100,330),(1440,50,130,360),
                 (1600,80,90,320),(1710,40,140,360),(1870,60,100,340)]
        for bx, _, bw, bh in bldgs:
            by = H - bh
            pygame.draw.rect(s, (8, 12, 42), (bx, by, bw, bh))
            for wy in range(by+8, H-8, 14):
                for wx in range(bx+8, bx+bw-8, 10):
                    if random.random() > 0.35:
                        col = random.choice([(0,180,255),(0,255,200),(255,200,0),(255,80,200)])
                        pygame.draw.rect(s, col, (wx, wy, 5, 8))
        return s

    def skip(self):
        self._done = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._done = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self._title_alpha >= 240:
                self._done = True

    def update(self, dt):
        super().update(dt)
        self._city_scroll += dt * 30
        if self._city_scroll >= W:
            self._city_scroll = 0
        _spawn_blue_particles(self._particles, 1)
        _update_particles(self._particles, dt)
        # Fade-ins
        self._title_alpha = min(255, self._title_alpha + dt * 80)
        if self._t > 1.5:
            self._sub_alpha = min(255, self._sub_alpha + dt * 100)
        if self._t > 2.5:
            self._press_alpha = min(255, self._press_alpha + dt * 120)
        # Vehicles
        for v in self._vehicles:
            v['x'] += v['speed'] * dt
            if v['x'] > W + 100:
                v['x'] = -120

    def draw(self, surf):
        surf.fill((0, 0, 0))
        t = self._t
        # Scrolling city BG
        sx = int(self._city_scroll)
        surf.blit(self._bg, (-sx, 0))
        surf.blit(self._bg, (W - sx, 0))
        # Overlay gradient
        grad = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(H):
            a = int(60 + i/H * 120)
            pygame.draw.line(grad, (0, 0, 12, a), (0, i), (W, i))
        surf.blit(grad, (0, 0))
        # Stars
        for sx2, sy, br in self._stars:
            a = int(br * (100 + math.sin(t*br+sx2)*30))
            pygame.draw.circle(surf, (200, 220, 255), (int(sx2), int(sy)), 1)

        # Vehicles (hover)
        for v in self._vehicles:
            vr = pygame.Rect(int(v['x']), int(v['y']), v['w'], 22)
            pygame.draw.rect(surf, (18, 22, 55), vr, border_radius=5)
            pygame.draw.rect(surf, v['color'], vr, 1, border_radius=5)
            gs = pygame.Surface((v['w'], 10), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (*v['color'][:3], 40), gs.get_rect())
            surf.blit(gs, (vr.x, vr.y+22), special_flags=pygame.BLEND_RGBA_ADD)

        # Particles
        _blue_particles(surf, self._particles, t)

        # Title: PLANZARA
        if self._title_alpha > 4:
            for i, ch in enumerate("PLANZARA"):
                off = math.sin(t * 1.2 + i * 0.5) * 4
                cs = self.f_xl.render(ch, True, (0, 200, 255))
                cs.set_alpha(int(self._title_alpha))
                tx2 = W//2 - len("PLANZARA")*42//2 + i*42
                surf.blit(cs, (tx2, H//2 - 100 + int(off)))
            # Glow
            gs2 = pygame.Surface((W, 100), pygame.SRCALPHA)
            a2 = int(self._title_alpha * 0.12)
            pygame.draw.ellipse(gs2, (0, 180, 255, a2), (W//2-250, 10, 500, 80))
            surf.blit(gs2, (0, H//2-110), special_flags=pygame.BLEND_RGBA_ADD)

        # Subtitle
        if self._sub_alpha > 4:
            sub = self.f_sm.render("— The Timeline Beyond Time —", True, (100, 170, 230))
            sub.set_alpha(int(self._sub_alpha))
            surf.blit(sub, (W//2 - sub.get_width()//2, H//2 - 30))

        # Press Enter
        if self._press_alpha > 4:
            pulse = int(self._press_alpha * (0.6 + math.sin(t*3)*0.4))
            pe = self.f_md.render("PRESS  ENTER  TO  START", True, (0, 220, 255))
            pe.set_alpha(max(0, min(255, pulse)))
            surf.blit(pe, (W//2 - pe.get_width()//2, H//2 + 60))

        # Bottom credits
        cred = self.f_xs.render("PLANZARA  ·  Chapter I  ·  2187", True, (40, 70, 120))
        surf.blit(cred, (W//2 - cred.get_width()//2, H - 28))


# ══════════════════════════════════════════════════════════════════════
# 3. PHONE CALL CUTSCENE
# ══════════════════════════════════════════════════════════════════════

_PHONE_LINES = [
    ("Mits",  "Yo, Suzen."),
    ("Suzen", "Mits, come to the academy immediately."),
    ("Mits",  "Why?"),
    ("Suzen", "The project received approval."),
    ("Mits",  "Wait… the dinosaur era project?"),
    ("Suzen", "Yes. Reza is already here."),
    ("Mits",  "No way…"),
]

class PhoneCallCutscene(CutsceneBase):
    def __init__(self, fonts, audio=None):
        super().__init__(fonts)
        self._audio = audio
        self._phase = 'ring'   # ring → call → done
        self._ring_t = 0.0
        self._line_idx = 0
        self._line_t   = 0.0
        self._line_pos = 0.0
        self._alpha    = 0.0
        self._ring_played = False

    def update(self, dt):
        super().update(dt)
        if self._phase == 'ring':
            self._ring_t += dt
            if not self._ring_played and self._audio:
                self._audio.play_sfx('phone')
                self._ring_played = True
            if self._ring_t > 2.5:
                self._phase = 'call'
        elif self._phase == 'call':
            self._alpha = min(220, self._alpha + dt * 400)
            if self._line_idx < len(_PHONE_LINES):
                txt = _PHONE_LINES[self._line_idx][1]
                self._line_pos = min(float(len(txt)), self._line_pos + dt * 36)
                self._line_t  += dt
                if self._line_t > 2.8 and self._line_pos >= len(txt):
                    self._line_idx += 1
                    self._line_t    = 0.0
                    self._line_pos  = 0.0
                    if self._audio: self._audio.play_sfx('blip')
            else:
                self._phase = '_ending'
                self._line_t = 0.0
        elif self._phase == '_ending':
            self._line_t += dt
            if self._line_t > 1.5:
                self._done = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_z, pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                if self._phase == 'call':
                    txt = _PHONE_LINES[self._line_idx][1] if self._line_idx < len(_PHONE_LINES) else ''
                    if self._line_pos < len(txt):
                        self._line_pos = float(len(txt))
                    else:
                        self._line_idx += 1
                        self._line_t   = 0.0
                        self._line_pos = 0.0
                        if self._audio: self._audio.play_sfx('blip')
                        if self._line_idx >= len(_PHONE_LINES):
                            self._phase = '_ending'
                elif self._phase == 'ring':
                    self._phase = 'call'
            elif event.key == pygame.K_ESCAPE:
                self._done = True

    def draw(self, surf):
        surf.fill((3, 5, 22))
        t = self._t
        # Shimmer background
        for i in range(H):
            a = int(8 + i/H*15)
            pygame.draw.line(surf, (0, a//3, a), (0, i), (W, i))

        if self._phase == 'ring':
            # Ringtone animation
            rings = int(t * 3) % 3
            for i in range(3):
                a2 = 200 if i == rings else 80
                r2 = 60 + i * 30
                rs = pygame.Surface((r2*2, r2*2), pygame.SRCALPHA)
                pygame.draw.circle(rs, (0, 180, 255, a2), (r2, r2), r2, 3)
                surf.blit(rs, (W//2-r2, H//2-r2), special_flags=pygame.BLEND_RGBA_ADD)
            # Phone icon
            pygame.draw.rect(surf, (18, 28, 70), (W//2-30, H//2-50, 60, 100), border_radius=8)
            pygame.draw.rect(surf, (0, 180, 255), (W//2-30, H//2-50, 60, 100), 2, border_radius=8)
            ct = self.f_sm.render("INCOMING CALL", True, (0, 200, 255))
            surf.blit(ct, (W//2 - ct.get_width()//2, H//2 + 60))
            cn = self.f_md.render("SUZEN ARCLIGHT", True, (180, 210, 255))
            surf.blit(cn, (W//2 - cn.get_width()//2, H//2 + 86))
        elif self._phase in ('call', '_ending') and self._alpha > 4:
            # Caller info
            cal = pygame.Surface((380, 60), pygame.SRCALPHA)
            pygame.draw.rect(cal, (5, 15, 55, 210), cal.get_rect(), border_radius=8)
            pygame.draw.rect(cal, (0, 155, 255, 180), cal.get_rect(), 1, border_radius=8)
            cn = self.f_md.render("☎  SUZEN ARCLIGHT", True, (0, 220, 255))
            cal.blit(cn, (20, 18))
            cal.set_alpha(int(self._alpha))
            surf.blit(cal, (W//2-190, 80))

            # Dialogue box
            if self._line_idx < len(_PHONE_LINES):
                spk, txt = _PHONE_LINES[self._line_idx]
                shown = txt[:int(self._line_pos)]
                box   = pygame.Surface((W - 80, 100), pygame.SRCALPHA)
                pygame.draw.rect(box, (5, 12, 45, 215), box.get_rect(), border_radius=10)
                pygame.draw.rect(box, (0, 155, 255, 160), box.get_rect(), 2, border_radius=10)
                pygame.draw.rect(box, (0, 155, 255, 220), (0, 0, 5, 100))
                sn = self.f_xs.render(spk, True, (0, 210, 255))
                st = self.f_sm.render(shown, True, (200, 218, 255))
                box.blit(sn, (14, 10))
                box.blit(st, (14, 38))
                box.set_alpha(int(self._alpha))
                surf.blit(box, (40, H - 150))
                prog = self.f_xs.render(f"{self._line_idx+1}/{len(_PHONE_LINES)}", True, (70,100,160))
                surf.blit(prog, (W - 80, H - 130))


# ══════════════════════════════════════════════════════════════════════
# 4. TIME TRAVEL CUTSCENE  (portal activation + arrival 2026)
# ══════════════════════════════════════════════════════════════════════

_TRAVEL_LINES = [
    ("Mits",  "Uh… was it supposed to do that?!"),
    ("Reza",  "No—!"),
]
_ARRIVAL_LINES = [
    ("Mits",  "...This doesn't look prehistoric."),
    ("Suzen", "Something went wrong."),
    ("Reza",  "No signal…"),
    ("Mits",  "What does that mean?"),
    ("Reza",  "We cannot reconnect."),
]

class TimeTravelCutscene(CutsceneBase):
    def __init__(self, fonts, audio=None):
        super().__init__(fonts)
        self._audio    = audio
        self._phase    = 'charge'   # charge → portal → flash → arrival → done
        self._phase_t  = 0.0
        self._particles= []
        self._glitch_t = 0.0
        self._lines    = _TRAVEL_LINES
        self._line_idx = 0
        self._line_pos = 0.0
        self._line_t   = 0.0
        self._flash_a  = 0.0
        self._arr_phase= 'text'
        self._arr_idx  = 0
        self._arr_pos  = 0.0
        self._arr_t    = 0.0

    def update(self, dt):
        super().update(dt)
        self._phase_t += dt
        _update_particles(self._particles, dt)
        pt = self._phase_t
        if self._phase == 'charge':
            # spawn portal particles
            for _ in range(int(pt*3)+2):
                a = random.uniform(0, math.pi*2)
                r2 = random.uniform(60, 120) * (0.5 + pt*0.1)
                col = random.choice([(0,180,255),(0,255,220),(100,140,255)])
                self._particles.append({
                    'x': W//2 + math.cos(a)*r2, 'y': H//2 + math.sin(a)*r2,
                    'vx': -math.cos(a)*40, 'vy': -math.sin(a)*40,
                    'life': 0.8, 'max': 0.8, 'r': random.randint(2,5), 'c': col,
                })
            if pt > 4.0:
                self._phase = 'portal'
                self._phase_t = 0.0
                if self._audio: self._audio.play_sfx('portal')
        elif self._phase == 'portal':
            for _ in range(8):
                a = random.uniform(0, math.pi*2)
                r2 = random.uniform(10, 200)
                col = random.choice([(0,180,255),(0,255,220),(200,100,255),(255,255,255)])
                self._particles.append({
                    'x': W//2 + math.cos(a)*r2, 'y': H//2 + math.sin(a)*r2,
                    'vx': math.cos(a)*120, 'vy': math.sin(a)*120,
                    'life': 0.5, 'max': 0.5, 'r': random.randint(1,4), 'c': col,
                })
            # Dialogue
            if self._line_idx < len(self._lines):
                txt = self._lines[self._line_idx][1]
                self._line_pos = min(float(len(txt)), self._line_pos + 36*dt)
                self._line_t  += dt
                if self._line_t > 2.0 and self._line_pos >= len(txt):
                    self._line_idx += 1; self._line_t = 0.0; self._line_pos = 0.0
            if pt > 3.5:
                self._phase = 'flash'
                self._phase_t = 0.0
                if self._audio: self._audio.play_sfx('glitch')
        elif self._phase == 'flash':
            self._flash_a = min(255, self._flash_a + dt * 600)
            if self._flash_a >= 255 and pt > 0.6:
                self._phase = 'arrival'
                self._phase_t = 0.0
                self._flash_a = 255.0
        elif self._phase == 'arrival':
            self._flash_a = max(0, self._flash_a - dt*180)
            if self._arr_idx < len(_ARRIVAL_LINES):
                txt = _ARRIVAL_LINES[self._arr_idx][1]
                self._arr_pos = min(float(len(txt)), self._arr_pos + 36*dt)
                self._arr_t  += dt
                if self._arr_t > 3.0 and self._arr_pos >= len(txt):
                    self._arr_idx += 1; self._arr_t = 0.0; self._arr_pos = 0.0
            else:
                if pt > 2.0: self._done = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_z, pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                if self._phase == 'arrival':
                    if self._arr_pos < len(_ARRIVAL_LINES[self._arr_idx][1]) \
                            if self._arr_idx < len(_ARRIVAL_LINES) else False:
                        self._arr_pos = float(len(_ARRIVAL_LINES[self._arr_idx][1]))
                    else:
                        self._arr_idx += 1; self._arr_t = 0.0; self._arr_pos = 0.0
                        if self._arr_idx >= len(_ARRIVAL_LINES):
                            self._done = True
            elif event.key == pygame.K_ESCAPE:
                self._done = True

    def draw(self, surf):
        surf.fill((2, 4, 20))
        t  = self._t
        pt = self._phase_t

        if self._phase in ('charge', 'portal'):
            # Ambient energy glow
            gs = pygame.Surface((W, H), pygame.SRCALPHA)
            r = int(80 + math.sin(t*4)*30) + int(pt*20)
            a = int(40 + math.sin(t*3)*15)
            pygame.draw.circle(gs, (0, 160, 255, a), (W//2, H//2), r)
            surf.blit(gs, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            # Portal ring
            for ri in range(5):
                ra  = int((60 + ri*25) * (0.8 + pt*0.1))
                al  = int(200 - ri*30)
                angle_off = t * (1.5 + ri*0.3)
                ring_s = pygame.Surface((ra*2+4, ra*2+4), pygame.SRCALPHA)
                pygame.draw.circle(ring_s, (0, 200, 255, al), (ra+2, ra+2), ra, 3)
                ring_s = pygame.transform.rotate(ring_s, angle_off*30)
                rx2 = ring_s.get_width()//2; ry2 = ring_s.get_height()//2
                surf.blit(ring_s, (W//2-rx2, H//2-ry2), special_flags=pygame.BLEND_RGBA_ADD)

            # Glitch lines
            if self._phase == 'portal' and random.random() < 0.3:
                gy2 = random.randint(0, H)
                gw2 = random.randint(80, 400)
                gx2 = random.randint(0, W-gw2)
                gs2 = pygame.Surface((gw2, 3), pygame.SRCALPHA)
                gs2.fill((200, 220, 255, random.randint(40, 120)))
                surf.blit(gs2, (gx2, gy2))

        elif self._phase == 'arrival':
            # Dim school-like interior
            for i in range(H):
                c = int(30 + i/H*15)
                pygame.draw.line(surf, (c, c-2, c-5), (0, i), (W, i))
            # Lockers on wall
            for lx2 in range(60, W-60, 60):
                pygame.draw.rect(surf, (100, 95, 85), (lx2, 80, 50, 80), border_radius=2)
                pygame.draw.rect(surf, (80, 75, 68), (lx2, 80, 50, 80), 1)
            # Characters stood confused
            bs = 5
            from sprites import draw_char, MITS, SUZEN, REZA, CW, CH
            for i, art in enumerate([MITS, SUZEN, REZA]):
                ox = W//2 - CW*bs + i*100 - 50
                oy = H//2 - CH*bs//2 + 40
                draw_char(surf, art, ox, oy, bs)
            # Arrival dialogue
            if self._arr_idx < len(_ARRIVAL_LINES):
                spk, txt = _ARRIVAL_LINES[self._arr_idx]
                shown = txt[:int(self._arr_pos)]
                box   = pygame.Surface((W-80, 92), pygame.SRCALPHA)
                pygame.draw.rect(box, (5,12,45,215), box.get_rect(), border_radius=10)
                pygame.draw.rect(box, (0,155,255,160), box.get_rect(), 2, border_radius=10)
                pygame.draw.rect(box, (0,155,255,220), (0,0,5,92))
                sn = self.f_xs.render(spk, True, (0,210,255))
                st = self.f_sm.render(shown, True, (200,218,255))
                box.blit(sn, (14,8)); box.blit(st, (14,34))
                surf.blit(box, (40, H-140))

        _blue_particles(surf, self._particles, t)

        # Flash overlay
        if self._flash_a > 0:
            fb = pygame.Surface((W, H))
            fb.fill((255, 255, 255))
            fb.set_alpha(int(self._flash_a))
            surf.blit(fb, (0, 0))

        if self._phase in ('charge','portal') and self._line_idx < len(self._lines):
            spk, txt = self._lines[self._line_idx]
            shown    = txt[:int(self._line_pos)]
            box      = pygame.Surface((W-80, 80), pygame.SRCALPHA)
            pygame.draw.rect(box, (5,12,45,200), box.get_rect(), border_radius=8)
            pygame.draw.rect(box, (0,155,255,140), box.get_rect(), 1, border_radius=8)
            sn = self.f_xs.render(spk, True, (0,210,255))
            st = self.f_sm.render(shown, True, (200,218,255))
            box.blit(sn,(12,8)); box.blit(st,(12,32))
            surf.blit(box, (40, H-120))


# ══════════════════════════════════════════════════════════════════════
# 5. TEA SHOP REVELATION  (timeline reveal + TV news)
# ══════════════════════════════════════════════════════════════════════

_TEA_LINES = [
    ("Tea Shop Owner", "What do you want?"),
    ("Mits",           "Three teas."),
    ("Tea Shop Owner", "That'll be 60 rupees."),
    ("Mits",           "It was normal money yesterday…"),
    ("Tea Shop Owner", "Is this some movie prop?"),
    ("Reza",           "Our currency doesn't exist here…"),
    ("Mits",           "This really is the past…"),
    ("Reza",           "No… It's worse than that."),
    ("Suzen",          "What do you mean?"),
    ("Reza",           "This timeline was sealed."),
    ("Mits",           "By who?"),
    ("Reza",           "Captain Opra."),
    ("Mits",           "The same Captain Opra from timeline history?"),
    ("Reza",           "Yes. He disappeared long ago."),
    ("Reza",           "Some records say he abandoned Planzara."),
    ("Reza",           "Others say he became obsessed with timelines."),
    ("Suzen",          "Then why would he seal an entire timeline?"),
    ("Reza",           "I don't know."),
    ("Reza",           "But if this really is the sealed timeline…"),
    ("Reza",           "Then we may be trapped here permanently."),
]

class TeaShopRevelation(CutsceneBase):
    def __init__(self, fonts, audio=None):
        super().__init__(fonts)
        self._audio   = audio
        self._idx     = 0
        self._pos     = 0.0
        self._t_line  = 0.0
        self._alpha   = 0.0
        self._rain_drops = [{'x': random.randint(0,W), 'y': random.randint(0,H),
                             'speed': random.uniform(300,500)} for _ in range(120)]

    def update(self, dt):
        super().update(dt)
        self._alpha = min(220, self._alpha + dt*600)
        for d in self._rain_drops:
            d['y'] += d['speed']*dt
            if d['y'] > H: d['y'] = random.randint(-20,0); d['x'] = random.randint(0,W)
        if self._idx < len(_TEA_LINES):
            txt = _TEA_LINES[self._idx][1]
            self._pos = min(float(len(txt)), self._pos + 38*dt)
            self._t_line += dt
            if self._t_line > 3.2 and self._pos >= len(txt):
                self._idx += 1; self._t_line = 0.0; self._pos = 0.0
                if self._audio: self._audio.play_sfx('blip')
        else:
            if self._t_line == 0.0: self._t_line = 0.001
            self._t_line += dt
            if self._t_line > 2.0: self._done = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_z, pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                if self._idx < len(_TEA_LINES):
                    txt = _TEA_LINES[self._idx][1]
                    if self._pos < len(txt):
                        self._pos = float(len(txt))
                    else:
                        self._idx += 1; self._t_line = 0.0; self._pos = 0.0
                        if self._audio: self._audio.play_sfx('blip')
                        if self._idx >= len(_TEA_LINES): self._done = True
                else:
                    self._done = True
            elif event.key == pygame.K_ESCAPE:
                self._done = True

    def draw(self, surf):
        # Tea shop interior
        for i in range(H):
            c = int(18 + i/H*10)
            pygame.draw.line(surf, (c+8, c+4, c), (0, i), (W, i))
        # Rain on window
        rs = pygame.Surface((W, H), pygame.SRCALPHA)
        for d in self._rain_drops:
            pygame.draw.line(rs, (120,140,200,40),
                             (int(d['x']), int(d['y'])), (int(d['x'])+1, int(d['y'])+14), 1)
        surf.blit(rs, (0, 0))
        # Window glow (warm)
        ws2 = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.ellipse(ws2, (255, 180, 100, 22), (W//2-200, -50, 400, 200))
        surf.blit(ws2, (0, 0))
        # Dialogue
        if self._alpha > 4 and self._idx < len(_TEA_LINES):
            spk, txt = _TEA_LINES[self._idx]
            shown = txt[:int(self._pos)]
            bx2, by2, bw2, bh2 = 30, H-148, W-60, 120
            box = pygame.Surface((bw2, bh2), pygame.SRCALPHA)
            pygame.draw.rect(box, (6,12,42,min(int(self._alpha),215)), (0,0,bw2,bh2), border_radius=10)
            pygame.draw.rect(box, (0,155,255,min(int(self._alpha),170)), (0,0,bw2,bh2), 2, border_radius=10)
            pygame.draw.rect(box, (0,155,255,220), (0,0,5,bh2))
            sn = self.f_xs.render(f"● {spk}", True, (0,210,255))
            st = self.f_sm.render(shown, True, (200,218,255))
            box.blit(sn,(14,10)); box.blit(st,(14,40))
            # Progress
            pg = self.f_xs.render(f"{self._idx+1}/{len(_TEA_LINES)}", True, (70,100,160))
            box.blit(pg,(bw2-pg.get_width()-10,8))
            surf.blit(box,(bx2,by2))
            # Speaker label
            sname = pygame.Surface((self.f_xs.size(f"● {spk}")[0]+18, 28), pygame.SRCALPHA)
            pygame.draw.rect(sname,(5,18,58,210),sname.get_rect(),border_radius=5)
            pygame.draw.rect(sname,(0,140,220,180),sname.get_rect(),1,border_radius=5)
            sname.blit(self.f_xs.render(f"● {spk}",True,(0,210,255)),(9,4))
            surf.blit(sname,(44,by2-30))
        # Hint
        ht = self.f_xs.render("Z/E/ENTER: Next  |  ESC: Skip", True, (60,90,140))
        surf.blit(ht, (W//2-ht.get_width()//2, H-26))


# ══════════════════════════════════════════════════════════════════════
# 6. CLIFFHANGER  (young Shanks + young Aizen, the lab incident)
# ══════════════════════════════════════════════════════════════════════

_CLIFF_LINES = [
    ("Trapped Scientist", "Please… don't leave me here…"),
    ("Young Captain Shanks", "Hold on! We're stabilizing the portal!"),
    ("Young Aizen Silvera",  "The temporal waves are changing…"),
    ("Young Captain Shanks", "Aizen, stop analyzing and help me!"),
    ("",  "[ Aizen writes: Timeline isolation possible… ]"),
    ("",  "[ Aizen writes: Disturbance prevents temporal reconnection… ]"),
    ("Young Captain Shanks", "No…!"),
    ("",  "[ The portal collapses. Silence. ]"),
    ("",  "[ Young Aizen slowly closes his notebook. ]"),
    ("Mrs. Silvera (offscreen)", "Aizen!"),
    ("",  "[ Then— ]"),
    ("",  "Mrs. Silvera is calling you, Mr. Silvera!"),
]

class CliffhangerCutscene(CutsceneBase):
    def __init__(self, fonts, audio=None):
        super().__init__(fonts)
        self._audio  = audio
        self._idx    = 0
        self._pos    = 0.0
        self._t_line = 0.0
        self._alpha  = 0.0
        self._fade   = 255.0
        self._scene_built = False
        self._freeze = False
        self._freeze_t = 0.0
        self._bg = None

    def _build_bg(self):
        s = pygame.Surface((W, H))
        # Damaged lab, emergency red
        for i in range(H):
            c = int(12 + i/H*20)
            pygame.draw.line(s, (c+8, c//3, c//3), (0, i), (W, i))
        # Lab equipment
        for bx2 in [60, 180, 680, 820]:
            pygame.draw.rect(s, (50, 40, 40), (bx2, 160, 80, 200), border_radius=3)
            pygame.draw.rect(s, (70, 55, 55), (bx2, 160, 80, 200), 1, border_radius=3)
        # Portal outline (center)
        for r2 in range(80, 160, 20):
            a2 = int(120 - (r2-80)*1.2)
            ps = pygame.Surface((r2*2+4, r2*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ps, (200, 100, 100, a2), (r2+2, r2+2), r2, 4)
            s.blit(ps, (W//2-r2-2, H//2-r2-40))
        return s

    def update(self, dt):
        super().update(dt)
        if not self._scene_built:
            self._bg = self._build_bg()
            self._scene_built = True
        self._fade = max(0, self._fade - dt*160)
        self._alpha = min(215, self._alpha + dt*400)
        if self._freeze:
            self._freeze_t += dt
            if self._freeze_t > 3.0: self._done = True
            return
        if self._idx < len(_CLIFF_LINES):
            txt = _CLIFF_LINES[self._idx][1]
            self._pos = min(float(len(txt)), self._pos + 36*dt)
            self._t_line += dt
            if self._t_line > 3.5 and self._pos >= len(txt):
                self._idx += 1; self._t_line = 0.0; self._pos = 0.0
                if self._audio: self._audio.play_sfx('blip')
                if self._idx >= len(_CLIFF_LINES):
                    self._freeze = True
        else:
            self._freeze = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_z,pygame.K_e,pygame.K_RETURN,pygame.K_SPACE):
                if not self._freeze and self._idx < len(_CLIFF_LINES):
                    txt = _CLIFF_LINES[self._idx][1]
                    if self._pos < len(txt):
                        self._pos = float(len(txt))
                    else:
                        self._idx += 1; self._t_line = 0.0; self._pos = 0.0
                        if self._audio: self._audio.play_sfx('blip')
                        if self._idx >= len(_CLIFF_LINES): self._freeze = True
                else:
                    self._done = True
            elif event.key == pygame.K_ESCAPE:
                self._done = True

    def draw(self, surf):
        if self._bg:
            surf.blit(self._bg, (0, 0))
        else:
            surf.fill((12, 4, 4))

        t = self._t
        # Alarm strobe
        if int(t*3) % 2 == 0 and not self._freeze:
            flash_s = pygame.Surface((W, H), pygame.SRCALPHA)
            flash_s.fill((200, 0, 0, 15))
            surf.blit(flash_s, (0, 0))

        # Characters
        bs = 4
        from sprites import draw_char, YOUNG_AIZEN, YOUNG_SHANKS, CW, CH
        draw_char(surf, YOUNG_SHANKS, W//2 - 180, H//2 - CH*bs//2 + 20, bs)
        draw_char(surf, YOUNG_AIZEN, W//2 + 80,  H//2 - CH*bs//2 + 20, bs)

        # Frozen: screen pause effect
        if self._freeze:
            f_overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            f_a = min(100, int(self._freeze_t * 60))
            f_overlay.fill((0, 0, 30, f_a))
            surf.blit(f_overlay, (0, 0))

        # Dialogue
        if self._alpha > 4 and self._idx < len(_CLIFF_LINES):
            spk, txt2 = _CLIFF_LINES[self._idx]
            shown    = txt2[:int(self._pos)]
            is_narr  = spk == ''
            col      = (220, 200, 180) if is_narr else (200, 218, 255)
            bh2      = 96
            box      = pygame.Surface((W-80, bh2), pygame.SRCALPHA)
            pygame.draw.rect(box, (8,4,4,210),(0,0,W-80,bh2),border_radius=10)
            bcol2    = (180, 60, 60, 140) if is_narr else (0,155,255,140)
            pygame.draw.rect(box, bcol2,(0,0,W-80,bh2),2,border_radius=10)
            if not is_narr:
                sn = self.f_xs.render(f"● {spk}", True, (255,160,160))
                box.blit(sn,(14,10))
            st       = self.f_sm.render(shown, True, col)
            box.blit(st,(14,38 if not is_narr else 24))
            surf.blit(box,(40,H-140))

        # Fade from black
        if self._fade > 0:
            fb = pygame.Surface((W,H)); fb.fill((0,0,0))
            fb.set_alpha(int(self._fade)); surf.blit(fb,(0,0))


# ══════════════════════════════════════════════════════════════════════
# 7. CHAPTER END
# ══════════════════════════════════════════════════════════════════════

class ChapterEndCutscene(CutsceneBase):
    def __init__(self, fonts, audio=None):
        super().__init__(fonts)
        self._audio      = audio
        self._particles  = []
        self._fade_in    = 255.0
        self._logo_a     = 0.0
        self._ch1_a      = 0.0
        self._tbc_a      = 0.0
        self._phase      = 'logo'   # logo → ch1 → tbc → hold → done
        self._phase_t    = 0.0

    def update(self, dt):
        super().update(dt)
        self._phase_t += dt
        _spawn_blue_particles(self._particles, 2)
        _update_particles(self._particles, dt)
        self._fade_in = max(0, self._fade_in - dt * 120)
        if self._phase == 'logo':
            self._logo_a = min(255, self._logo_a + dt * 100)
            if self._phase_t > 3.0:
                self._phase = 'ch1'; self._phase_t = 0.0
        elif self._phase == 'ch1':
            self._ch1_a = min(255, self._ch1_a + dt*120)
            if self._phase_t > 3.0:
                self._phase = 'tbc'; self._phase_t = 0.0
        elif self._phase == 'tbc':
            self._tbc_a = min(255, self._tbc_a + dt*100)
            if self._phase_t > 4.0:
                self._phase = 'hold'; self._phase_t = 0.0
        elif self._phase == 'hold':
            if self._phase_t > 3.5:
                self._done = True

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE,
                             pygame.K_z, pygame.K_e):
                if self._tbc_a > 200:
                    self._done = True

    def draw(self, surf):
        surf.fill((0, 0, 0))
        t = self._t
        # Stars
        for i in range(80):
            sx = (i * 137 + int(t*8)) % W
            sy = (i * 97  + int(t*4)) % H
            a2 = int(100 + math.sin(t+i)*50)
            pygame.draw.circle(surf, (180, 200, 255), (sx, sy), 1)

        _blue_particles(surf, self._particles, t)

        # PLANZARA logo
        if self._logo_a > 4:
            for i, ch in enumerate("PLANZARA"):
                off = math.sin(t * 1.0 + i * 0.6) * 5
                cs = self.f_xl.render(ch, True, (0, 200, 255))
                cs.set_alpha(int(self._logo_a))
                tx2 = W//2 - len("PLANZARA")*40//2 + i*40
                surf.blit(cs, (tx2, H//2 - 120 + int(off)))
            # Underline glow
            gs = pygame.Surface((460, 4), pygame.SRCALPHA)
            gs.fill((0, 200, 255, int(self._logo_a*0.6)))
            surf.blit(gs, (W//2 - 230, H//2 - 88))

        # CHAPTER 1 COMPLETE
        if self._ch1_a > 4:
            cs = self.f_lg.render("CHAPTER  I  COMPLETE", True, (180, 220, 255))
            cs.set_alpha(int(self._ch1_a))
            surf.blit(cs, (W//2 - cs.get_width()//2, H//2 - 20))

        # TO BE CONTINUED
        if self._tbc_a > 4:
            pulse = int(self._tbc_a * (0.7 + math.sin(t*2.5)*0.3))
            ts2   = self.f_md.render("TO  BE  CONTINUED...", True, (100, 160, 220))
            ts2.set_alpha(max(0, min(255, pulse)))
            surf.blit(ts2, (W//2 - ts2.get_width()//2, H//2 + 60))

        # Fade from black
        if self._fade_in > 0:
            fb = pygame.Surface((W, H)); fb.fill((0,0,0))
            fb.set_alpha(int(self._fade_in)); surf.blit(fb,(0,0))

        if self._tbc_a > 100:
            ht = self.f_xs.render("Press ENTER or SPACE to continue", True, (50,80,130))
            surf.blit(ht, (W//2-ht.get_width()//2, H-28))


# ══════════════════════════════════════════════════════════════════════
# 8. CHARACTER INTRO CARDS  (re-exported helper)
# ══════════════════════════════════════════════════════════════════════

class CharIntroSequence:
    """Plays intro cards for a list of characters in sequence."""
    def __init__(self, chars, fonts):
        """chars: list of (name, title, art_data)"""
        self._chars  = chars
        self._fonts  = fonts
        self._idx    = 0
        self._done   = False
        self._card_t = 0.0
        self._alpha  = 0.0
        self._phase  = 'in'    # in → hold → out
        self._dur    = 3.2

    @property
    def done(self): return self._done

    def update(self, dt):
        self._card_t += dt
        if self._phase == 'in':
            self._alpha = min(255, self._alpha + dt*350)
            if self._alpha >= 255: self._phase = 'hold'
        elif self._phase == 'hold':
            if self._card_t > self._dur - 0.8: self._phase = 'out'
        elif self._phase == 'out':
            self._alpha = max(0, self._alpha - dt*350)
            if self._alpha <= 0:
                self._idx   += 1
                self._card_t = 0.0
                self._phase  = 'in'
                if self._idx >= len(self._chars):
                    self._done = True

    def draw(self, surf, W, H):
        if self._done or self._idx >= len(self._chars): return
        name, title, _ = self._chars[self._idx]
        al = int(self._alpha)
        pw, ph = 460, 110
        px, py = 80, H//2 - ph//2
        s = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(s, (5,10,38,min(al,210)), (0,0,pw,ph), border_radius=8)
        pygame.draw.rect(s, (0,175,255,min(al,180)), (0,0,pw,ph), 2, border_radius=8)
        pygame.draw.rect(s, (0,140,200,min(al,220)), (0,0,5,ph))
        n  = self._fonts[1].render(name,  True, (0,215,255)); n.set_alpha(al)
        tt = self._fonts[3].render(title, True, (155,195,235)); tt.set_alpha(al)
        s.blit(n,  (18,18))
        s.blit(tt, (18,62))
        pygame.draw.line(s,(0,140,200,min(al,150)),(18,58),(pw-18,58),1)
        surf.blit(s, (px, py))