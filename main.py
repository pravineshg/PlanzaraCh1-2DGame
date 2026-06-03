"""
PLANZARA — The Timeline Beyond Time
main.py  |  Chapter I  |  Year 2187

Full game loop: scene manager · gameplay · cutscenes · UI · audio.
Resolution: 960×540  |  Python + Pygame only.
"""

import pygame, sys, math, random

# ══════════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════════
W, H = 960, 540
FPS  = 60

# Scene identifiers
SC_INTRO     = 'intro'
SC_TITLE     = 'title'
SC_APT       = 'apartment'
SC_STOCK     = 'stock_market'
SC_PHONE     = 'phone_call'
SC_APT2      = 'apartment_exit'
SC_VALORA    = 'valora_street'
SC_SCOOTY    = 'scooty_ride'
SC_ACADEMY   = 'academy_hall'
SC_LAB_CARDS = 'lab_intro_cards'
SC_LAB_DIAG  = 'lab_dialogue'
SC_TRAVEL    = 'time_travel'
SC_SCHOOL    = 'school_2026'
SC_STREETS   = 'streets_2026'
SC_TEA       = 'tea_revelation'
SC_CLIFF     = 'cliffhanger'
SC_END       = 'chapter_end'


# ══════════════════════════════════════════════════════════════════════
# SCOOTY MINIGAME  (self-contained, no external dependencies)
# ══════════════════════════════════════════════════════════════════════

class ScootyRide:
    """
    Energetic hover-scooty ride from Valora City to the Academy.
    Player dodges drones and traffic on a cyberpunk highway.
    """

    _DLG = [
        (2.2, "Mits", "I still can't believe they approved student time travel."),
        (7.0, "Mits", "If we actually see dinosaurs, I'm recording everything."),
    ]

    def __init__(self, fonts, audio=None):
        self._f_xl, self._f_lg, self._f_md, self._f_sm, self._f_xs = fonts
        self._audio   = audio
        self._done    = False
        self._t       = 0.0

        # Rider
        self._ry      = float(H // 2)
        self._scroll  = 0.0
        self._spd_x   = 240.0

        # HP + invincibility
        self._hp      = 3
        self._inv_t   = 0.0

        # Progress
        self._prog    = 0.0
        self._done_t  = 0.0

        # Obstacles
        self._obs = [
            {'x': W + 200 + i * 220 + random.randint(0, 60),
             'y': random.randint(150, H - 150),
             'w': random.randint(44, 68), 'h': 26}
            for i in range(14)
        ]

        # Particles (engine exhaust)
        self._parts = []

        # Timed dialogue
        self._dlg_shown = [False] * len(self._DLG)
        self._dlg_idx   = -1
        self._dlg_t     = 0.0

        # Notification
        self._notif   = ''
        self._notif_t = 0.0

        # Static background buildings (deterministic)
        rng = random.Random(42)
        self._bg_bldgs = [
            (i * 95, H - (70 + rng.randint(0, 90)), 75 + rng.randint(0, 30))
            for i in range(16)
        ]

    # ── public ────────────────────────────────────────────────────────
    @property
    def done(self): return self._done

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._done = True

    def update(self, dt):
        self._t      += dt
        self._scroll += self._spd_x * dt
        self._prog    = min(1.0, self._scroll / 3600.0)
        self._inv_t   = max(0.0, self._inv_t - dt)

        # Player vertical movement
        keys = pygame.key.get_pressed()
        vy   = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:   vy = -220
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: vy =  220
        self._ry = max(110.0, min(H - 110.0, self._ry + vy * dt))

        # Engine exhaust particles
        if random.random() < 0.55:
            self._parts.append({
                'x': 100.0 - 24, 'y': self._ry + random.uniform(-6, 6),
                'vx': random.uniform(-130, -50), 'vy': random.uniform(-12, 12),
                'life': random.uniform(0.3, 0.55), 'max': 0.55,
                'col': random.choice([(0,200,255),(0,255,180),(255,200,0)]),
                'r': random.randint(1, 3),
            })
        alive = []
        for p in self._parts:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['life'] -= dt
            if p['life'] > 0:
                alive.append(p)
        self._parts = alive

        # Scroll obstacles
        for ob in self._obs:
            ob['x'] -= self._spd_x * dt
            if ob['x'] < -80:
                ob['x'] = W + random.randint(120, 350)
                ob['y'] = random.randint(120, H - 120)

        # Collision
        if self._inv_t <= 0:
            rx, ry = 100, int(self._ry)
            for ob in self._obs:
                ox, oy = int(ob['x']), int(ob['y'])
                if abs(rx - ox) < 36 and abs(ry - oy) < 28:
                    self._hp      = max(0, self._hp - 1)
                    self._inv_t   = 1.6
                    self._notif   = "COLLISION!"
                    self._notif_t = 1.2
                    if self._audio: self._audio.play_sfx('alert')
                    if self._hp <= 0:
                        self._hp    = 3  # respawn with full hp (arcade style)
                    break

        if self._notif_t > 0:
            self._notif_t -= dt

        # Timed dialogue
        for i, (trigger, spk, txt) in enumerate(self._DLG):
            if not self._dlg_shown[i] and self._t >= trigger:
                self._dlg_shown[i] = True
                self._dlg_idx      = i
                self._dlg_t        = 5.0
        if self._dlg_t > 0:
            self._dlg_t -= dt
            if self._dlg_t <= 0:
                self._dlg_idx = -1

        # Completion
        if self._prog >= 1.0:
            self._done_t += dt
            if self._done_t >= 1.8:
                self._done = True

    def draw(self, surf):
        # ── Sky gradient ──────────────────────────────────────────────
        for i in range(H):
            rr = int(3  + i / H * 10)
            gg = int(4  + i / H * 10)
            bb = int(18 + i / H * 28)
            pygame.draw.line(surf, (rr, gg, bb), (0, i), (W, i))

        # ── Parallax background skyline ───────────────────────────────
        bg_off = int(self._scroll * 0.28) % (16 * 95)
        for i, (bx, by, bw) in enumerate(self._bg_bldgs):
            sx = (bx - bg_off) % (16 * 95)
            pygame.draw.rect(surf, (8, 12, 44), (sx, by, bw, H - by))
            for wy in range(by + 8, H - 8, 14):
                for wx in range(sx + 6, sx + bw - 6, 10):
                    lit = (wx + wy + int(self._t * 0.4)) % 5 != 0
                    col = (0, 140, 200) if lit else (4, 6, 20)
                    pygame.draw.rect(surf, col, (wx, wy, 5, 8))

        # ── Road ──────────────────────────────────────────────────────
        road_y = H // 2 - 80
        pygame.draw.rect(surf, (22, 22, 34), (0, road_y, W, 220))
        pygame.draw.rect(surf, (32, 32, 50), (0, road_y, W, 220), 1)

        # Lane markings
        lane_off = int(self._scroll) % 120
        for lx in range(-lane_off, W + 120, 120):
            for ly in [road_y + 60, road_y + 120, road_y + 180]:
                pygame.draw.rect(surf, (55, 55, 70), (lx, ly, 60, 3))

        # Road edge neon
        a_edge = int(80 + math.sin(self._t * 2) * 20)
        pygame.draw.line(surf, (0, 200, 255), (0, road_y), (W, road_y), 2)
        pygame.draw.line(surf, (0, 200, 255), (0, road_y + 220), (W, road_y + 220), 2)

        # ── Obstacles (drones / hover-vehicles) ───────────────────────
        for ob in self._obs:
            ox, oy = int(ob['x']), int(ob['y'])
            # Body
            pygame.draw.rect(surf, (140, 28, 28), (ox - ob['w']//2, oy - 14, ob['w'], 28), border_radius=7)
            pygame.draw.rect(surf, (255, 70, 70), (ox - ob['w']//2, oy - 14, ob['w'], 28), 1, border_radius=7)
            # Rotors
            pygame.draw.ellipse(surf, (100, 20, 20), (ox - ob['w']//2 - 14, oy - 5, 14, 10))
            pygame.draw.ellipse(surf, (100, 20, 20), (ox + ob['w']//2,       oy - 5, 14, 10))
            # Glow
            gs = pygame.Surface((ob['w'] + 20, 20), pygame.SRCALPHA)
            pygame.draw.ellipse(gs, (255, 60, 60, 40), gs.get_rect())
            surf.blit(gs, (ox - ob['w']//2 - 10, oy + 14), special_flags=pygame.BLEND_RGBA_ADD)

        # ── Engine exhaust particles ───────────────────────────────────
        for p in self._parts:
            r  = max(1, p['r'])
            a2 = max(0, int(200 * (p['life'] / p['max'])))
            ps = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['col'], a2), (r + 1, r + 1), r)
            surf.blit(ps, (int(p['x'] - r - 1), int(p['y'] - r - 1)),
                      special_flags=pygame.BLEND_RGBA_ADD)

        # ── Player scooty ─────────────────────────────────────────────
        sx, sy = 100, int(self._ry)

        # Invincibility flicker
        visible = (self._inv_t <= 0) or (int(self._inv_t * 10) % 2 == 0)
        if visible:
            # Hover glow under scooty
            hs = pygame.Surface((120, 18), pygame.SRCALPHA)
            ha = int(50 + math.sin(self._t * 6) * 20)
            pygame.draw.ellipse(hs, (0, 200, 255, ha), hs.get_rect())
            surf.blit(hs, (sx - 60, sy + 18), special_flags=pygame.BLEND_RGBA_ADD)

            # Body
            pygame.draw.rect(surf, (14, 28, 70), (sx - 48, sy - 16, 96, 34), border_radius=12)
            pygame.draw.rect(surf, (0, 200, 255), (sx - 48, sy - 16, 96, 34), 2, border_radius=12)
            # Headlight
            pygame.draw.circle(surf, (200, 240, 255), (sx + 48, sy), 6)
            pygame.draw.circle(surf, (255, 255, 255), (sx + 48, sy), 3)

            # Rider (Mits) — simple sprite
            pygame.draw.circle(surf, (244, 228, 214), (sx, sy - 44), 12)  # head
            pygame.draw.rect(surf, (32, 140, 60), (sx - 12, sy - 36, 24, 30), border_radius=4)  # jacket
            pygame.draw.rect(surf, (18, 22, 60), (sx - 10, sy - 8, 8, 22), border_radius=3)   # leg L
            pygame.draw.rect(surf, (18, 22, 60), (sx + 2,  sy - 8, 8, 22), border_radius=3)   # leg R

        # ── Speed lines ───────────────────────────────────────────────
        spd_s = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(18):
            ly = random.randint(road_y + 10, road_y + 210)
            lw = random.randint(40, 120)
            la = random.randint(8, 22)
            pygame.draw.line(spd_s, (0, 180, 255, la), (random.randint(120, W), ly),
                             (random.randint(0, 100), ly), 1)
        surf.blit(spd_s, (0, 0))

        # ── HP indicator ──────────────────────────────────────────────
        for i in range(3):
            col  = (0, 255, 120) if i < self._hp else (55, 40, 40)
            bcol = (0, 200, 80)  if i < self._hp else (70, 55, 55)
            pygame.draw.circle(surf, col, (22 + i * 26, 22), 9)
            pygame.draw.circle(surf, bcol, (22 + i * 26, 22), 9, 1)
        hp_lbl = self._f_xs.render("HP", True, (80, 120, 170))
        surf.blit(hp_lbl, (8, 36))

        # ── Progress bar ──────────────────────────────────────────────
        bar_x = W // 2 - 160
        pygame.draw.rect(surf, (12, 18, 50), (bar_x, H - 38, 320, 14), border_radius=6)
        pw2 = int(self._prog * 316)
        if pw2 > 0:
            pygame.draw.rect(surf, (0, 200, 255), (bar_x + 2, H - 36, pw2, 10), border_radius=5)
        pygame.draw.rect(surf, (0, 150, 220), (bar_x, H - 38, 320, 14), 1, border_radius=6)
        dest = self._f_xs.render("◈  ACADEMY", True, (0, 200, 255))
        surf.blit(dest, (W // 2 - dest.get_width() // 2, H - 56))

        # ── Collision notification ────────────────────────────────────
        if self._notif_t > 0:
            a3 = min(255, int(self._notif_t * 200))
            ns = self._f_md.render(self._notif, True, (255, 80, 80))
            ns.set_alpha(a3)
            surf.blit(ns, (W // 2 - ns.get_width() // 2, H // 2 - 70))

        # ── Timed dialogue ────────────────────────────────────────────
        if 0 <= self._dlg_idx < len(self._DLG):
            _, spk, txt = self._DLG[self._dlg_idx]
            box = pygame.Surface((530, 68), pygame.SRCALPHA)
            pygame.draw.rect(box, (5, 12, 48, 215), box.get_rect(), border_radius=9)
            pygame.draw.rect(box, (0, 155, 255, 160), box.get_rect(), 1, border_radius=9)
            pygame.draw.rect(box, (0, 155, 255, 220), (0, 0, 4, 68))
            sn = self._f_xs.render(f"● {spk}", True, (0, 210, 255))
            st = self._f_sm.render(txt, True, (200, 220, 255))
            box.blit(sn, (12, 8))
            box.blit(st, (12, 30))
            surf.blit(box, (W // 2 - 265, H - 170))

        # ── Controls hint ─────────────────────────────────────────────
        ct = self._f_xs.render("W / S  ·  ↑ / ↓ : Dodge drones     ESC : Skip", True, (60, 95, 150))
        surf.blit(ct, (W // 2 - ct.get_width() // 2, H - 18))

        # ── Arrival banner ────────────────────────────────────────────
        if self._prog >= 1.0:
            a4 = min(255, int(self._done_t * 180))
            ar = self._f_lg.render("ARRIVED AT ACADEMY!", True, (0, 255, 160))
            ar.set_alpha(a4)
            surf.blit(ar, (W // 2 - ar.get_width() // 2, H // 2 - 30))


# ══════════════════════════════════════════════════════════════════════
# INTRO CARD WRAPPER  (normalises CharIntroSequence to .draw(surf) API)
# ══════════════════════════════════════════════════════════════════════

class _CardWrap:
    def __init__(self, seq): self._s = seq

    @property
    def done(self): return self._s.done

    def update(self, dt): self._s.update(dt)

    def draw(self, surf): self._s.draw(surf, W, H)

    def handle_event(self, event): pass


# ══════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════

def main():
    # ── Init ──────────────────────────────────────────────────────────
    pygame.init()
    pygame.display.set_caption("PLANZARA — The Timeline Beyond Time")
    screen = pygame.display.set_mode((W, H))
    clock  = pygame.time.Clock()

    # ── Fonts ──────────────────────────────────────────────────────────
    def _font(size, bold=False):
        for name in ('consolas', 'courier new', 'lucidaconsole', 'monospace'):
            try:
                f = pygame.font.SysFont(name, size, bold=bold)
                if f: return f
            except Exception:
                pass
        return pygame.font.SysFont(None, size, bold=bold)

    f_xl = _font(52, bold=True)   # title lettering
    f_lg = _font(30, bold=True)   # headings
    f_md = _font(21)              # dialogue, menus
    f_sm = _font(17)              # body text
    f_xs = _font(13)              # captions, hints

    # Font bundles expected by each module
    CUT_FONTS    = (f_xl, f_lg, f_md, f_sm, f_xs)  # CutsceneBase
    BATTLE_FONTS = (f_lg, f_md, f_sm, f_xs)          # StockMarketGame
    DLG_FONTS    = (f_md, f_sm, f_xs)                 # DialogueEngine

    # ── Module imports ────────────────────────────────────────────────
    from audio    import AudioManager
    from ui       import HUD, MissionBox, FadeScreen, PauseMenu, CharIntroCard
    from dialogue import DialogueEngine
    from player   import Player
    from npc      import NPC
    from missions import MissionManager
    import save_system
    from particles import ParticleSystem, RainSystem
    from maps     import get_map
    import sprites
    from cutscene import (IntroCinematic, TitleScreen, PhoneCallCutscene,
                          TimeTravelCutscene, TeaShopRevelation,
                          CliffhangerCutscene, ChapterEndCutscene,
                          CharIntroSequence)
    from battle import StockMarketGame

    # ── Core systems ──────────────────────────────────────────────────
    audio       = AudioManager()
    hud         = HUD(f_sm, f_xs)
    mission_box = MissionBox(f_sm, f_xs)
    fade        = FadeScreen()
    pause_menu  = PauseMenu(f_lg, f_md, f_sm)
    intro_card  = CharIntroCard(f_lg, f_sm)
    dialogue    = DialogueEngine(DLG_FONTS)
    missions    = MissionManager()
    game_state  = save_system.load() or save_system.default()
    psys        = ParticleSystem()

    # ── Static overlays ────────────────────────────────────────────────
    def _make_vignette():
        v = pygame.Surface((W, H), pygame.SRCALPHA)
        for i in range(72):
            a = int(i * 1.9)
            pygame.draw.rect(v, (0, 0, 0, a),
                             (i * 2, i, W - i * 4, H - i * 2), 3, border_radius=22)
        return v

    def _make_scanlines():
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 3):
            pygame.draw.line(s, (0, 0, 0, 14), (0, y), (W, y))
        return s

    vignette  = _make_vignette()
    scanlines = _make_scanlines()

    # ── Scene state ────────────────────────────────────────────────────
    scene       = SC_INTRO
    next_scene  = None
    active_cut  = None    # cutscene / minigame (has .update, .draw, .done)
    active_map  = None    # GameMap instance (has .camera, .draw_bg, .draw_fg)
    player      = None    # Player instance
    npcs        = []      # list of NPC
    rain        = None    # RainSystem (2026 scenes)
    lab_npcs    = []      # Suzen + Reza in lab dialogue scene

    # ── Transition helpers ─────────────────────────────────────────────
    def transition_to(new_sc, speed=320, color=(0, 0, 0)):
        nonlocal next_scene
        next_scene = new_sc
        fade.fade_out(speed, on_done=_commit_transition, color=color)

    def _commit_transition():
        nonlocal scene, next_scene, active_cut, active_map, player, npcs, rain, lab_npcs
        scene      = next_scene
        next_scene = None
        _enter_scene(scene)
        fade.fade_in(300)

    # ── Scene entry ────────────────────────────────────────────────────
    def _enter_scene(s):
        nonlocal active_cut, active_map, player, npcs, rain, lab_npcs

        # Reset shared state
        audio.stop_bgm(400)
        psys.clear()
        rain      = None
        npcs      = []
        lab_npcs  = []
        active_cut = None
        active_map = None
        player     = None
        if dialogue.active:
            # clear without callback
            dialogue.active and object.__setattr__(dialogue, 'active', False)
        try:
            dialogue.active = False
        except Exception:
            pass

        # ── 1. Opening cinematic ─────────────────────────────────────
        if s == SC_INTRO:
            active_cut = IntroCinematic(CUT_FONTS)
            audio.play_bgm('title')

        # ── 2. Title screen ──────────────────────────────────────────
        elif s == SC_TITLE:
            active_cut = TitleScreen(CUT_FONTS)
            audio.play_bgm('title')

        # ── 3. Apartment — check terminal mission ────────────────────
        elif s == SC_APT:
            active_map = get_map('apartment')
            player     = Player(320, 380, 'mits')
            active_map.camera.snap(player.cx, player.cy)
            missions.set('terminal')
            mission_box.show(missions.text(), missions.title())
            hud.location = "Valora City — Apt. 7F"
            hud.year     = "2187"
            audio.play_bgm('apartment')

        # ── 4. Stock market minigame ─────────────────────────────────
        elif s == SC_STOCK:
            active_cut = StockMarketGame(BATTLE_FONTS, audio)
            audio.play_bgm('apartment')

        # ── 5. Phone call cutscene ───────────────────────────────────
        elif s == SC_PHONE:
            active_cut = PhoneCallCutscene(CUT_FONTS, audio)
            audio.play_bgm('phone')

        # ── 6. Apartment — exit mission (after phone call) ───────────
        elif s == SC_APT2:
            active_map = get_map('apartment')
            player     = Player(320, 380, 'mits')
            active_map.camera.snap(player.cx, player.cy)
            missions.set('go_academy')
            missions.M['go_academy'].step = 0   # "Exit your apartment"
            mission_box.show(missions.text(), missions.title())
            hud.location = "Valora City — Apt. 7F"
            hud.year     = "2187"
            audio.play_bgm('apartment')

        # ── 7. Valora City street ─────────────────────────────────────
        elif s == SC_VALORA:
            active_map = get_map('valora')
            player     = Player(160, 560, 'mits')
            active_map.camera.snap(player.cx, player.cy)
            missions.set('go_academy')
            missions.M['go_academy'].step = 1   # "Reach your Flying Scooty"
            mission_box.show(missions.text(), missions.title())
            hud.location = "Valora City — Neon Boulevard"
            hud.year     = "2187"
            # Pedestrian NPCs
            for i, (nx, ny, art, fname) in enumerate([
                (500, 530, sprites.SUZEN, "Citizen"),
                (700, 510, sprites.REZA,  "Traveller"),
                (900, 545, sprites.MITS,  "Vendor"),
            ]):
                n = NPC(nx, ny, art, fname, wander=True)
                npcs.append(n)
            audio.play_bgm('scooty')

        # ── 8. Scooty ride minigame ───────────────────────────────────
        elif s == SC_SCOOTY:
            active_cut = ScootyRide(CUT_FONTS, audio)
            audio.play_bgm('scooty')

        # ── 9. Academy hall ───────────────────────────────────────────
        elif s == SC_ACADEMY:
            active_map = get_map('academy')
            player     = Player(480, 480, 'mits')
            active_map.camera.snap(player.cx, player.cy)
            missions.set('find_lab')
            mission_box.show(missions.text(), missions.title())
            hud.location = "Ad-itya Sam Rocks Academy"
            hud.year     = "2187"
            audio.play_bgm('lab')

        # ── 10. Lab character intro cards ─────────────────────────────
        elif s == SC_LAB_CARDS:
            seq = CharIntroSequence([
                ("SUZEN ARCLIGHT", "The Silent Observer", sprites.SUZEN),
                ("REZA SILVERA",   "The Timeline Genius",  sprites.REZA),
            ], CUT_FONTS)
            active_cut = _CardWrap(seq)
            audio.play_bgm('lab')

        # ── 11. Lab dialogue + time machine ──────────────────────────
        elif s == SC_LAB_DIAG:
            active_map = get_map('academy')
            player     = Player(300, 310, 'mits')
            player.can_move = False
            active_map.camera.snap(player.cx, player.cy)
            hud.location = "Lab-7 — Research Division"
            hud.year     = "2187"
            # Suzen + Reza as NPCs in the lab
            suzen = NPC(420, 300, sprites.SUZEN, "Suzen", fixed_face='down')
            reza  = NPC(530, 300, sprites.REZA,  "Reza",  fixed_face='left')
            lab_npcs = [suzen, reza]
            # Lab conversation lines
            _lab_lines = [
                ("Mits",  "I came as fast as I could."),
                ("Reza",  "You were still late."),
                ("Mits",  "Technically I arrived."),
                ("Suzen", "The machine is stable."),
                ("Reza",  "For now."),
                ("Suzen", "Destination set to dinosaur era."),
                ("Mits",  "We're actually doing this…"),
            ]
            dialogue.start(
                _lab_lines,
                on_done=lambda: transition_to(SC_TRAVEL, 400, (0, 0, 30))
            )
            audio.play_bgm('lab')

        # ── 12. Time travel cutscene ──────────────────────────────────
        elif s == SC_TRAVEL:
            active_cut = TimeTravelCutscene(CUT_FONTS, audio)
            audio.play_bgm('travel')

        # ── 13. School 2026 ───────────────────────────────────────────
        elif s == SC_SCHOOL:
            active_map = get_map('school_2026')
            player     = Player(480, 400, 'suzen')
            active_map.camera.snap(player.cx, player.cy)
            missions.set('escape')
            mission_box.show(missions.text(), missions.title())
            hud.location = "Unknown School Building"
            hud.year     = "2026"
            rain = RainSystem(W, H, 140)
            audio.play_bgm('school')

        # ── 14. Streets 2026 ──────────────────────────────────────────
        elif s == SC_STREETS:
            active_map = get_map('streets_2026')
            player     = Player(160, 450, 'suzen')
            active_map.camera.snap(player.cx, player.cy)
            missions.set('shelter')
            mission_box.show(missions.text(), missions.title())
            hud.location = "Unidentified City — 2026"
            hud.year     = "2026"
            rain = RainSystem(W, H, 200)
            audio.play_bgm('school')

        # ── 15. Tea shop revelation ───────────────────────────────────
        elif s == SC_TEA:
            active_cut = TeaShopRevelation(CUT_FONTS, audio)
            audio.play_bgm('tea')

        # ── 16. Cliffhanger ───────────────────────────────────────────
        elif s == SC_CLIFF:
            active_cut = CliffhangerCutscene(CUT_FONTS, audio)
            audio.play_bgm('cliff')

        # ── 17. Chapter end ───────────────────────────────────────────
        elif s == SC_END:
            active_cut = ChapterEndCutscene(CUT_FONTS, audio)
            audio.play_bgm('end')

    # ── Cutscene completion handler ────────────────────────────────────
    def _on_cutscene_done():
        _next = {
            SC_INTRO     : SC_TITLE,
            SC_TITLE     : SC_APT,
            SC_STOCK     : SC_PHONE,
            SC_PHONE     : SC_APT2,
            SC_SCOOTY    : SC_ACADEMY,
            SC_LAB_CARDS : SC_LAB_DIAG,
            SC_TRAVEL    : SC_SCHOOL,
            SC_TEA       : SC_CLIFF,
            SC_CLIFF     : SC_END,
            SC_END       : SC_TITLE,
        }
        dest = _next.get(scene)
        if dest:
            speed = 500 if scene == SC_TRAVEL else 320
            color = (255, 255, 255) if scene == SC_TRAVEL else (0, 0, 0)
            transition_to(dest, speed, color)

    # ── Interaction handler ────────────────────────────────────────────
    def handle_interact():
        if not player or not active_map:
            return
        # interact_point() returns WORLD coords
        ip  = player.interact_point()
        tag = active_map._check_interact(ip[0], ip[1])
        if tag is None:
            # Try a slightly larger probe
            for probe in [(ip[0], ip[1]-8), (ip[0], ip[1]+8),
                          (ip[0]-8, ip[1]), (ip[0]+8, ip[1])]:
                tag = active_map._check_interact(probe[0], probe[1])
                if tag: break
        if tag is None:
            return
        audio.play_sfx('confirm')
        _INTERACT_TABLE = {
            (SC_APT,     'terminal')     : SC_STOCK,
            (SC_APT2,    'door')         : SC_VALORA,
            (SC_VALORA,  'scooty')       : SC_SCOOTY,
            (SC_VALORA,  'academy_gate') : SC_ACADEMY,
            (SC_ACADEMY, 'lab_door')     : SC_LAB_CARDS,
            (SC_SCHOOL,  'exit_door')    : SC_STREETS,
            (SC_SCHOOL,  'rooftop_door') : SC_STREETS,
            (SC_STREETS, 'tea_shop')     : SC_TEA,
        }
        dest = _INTERACT_TABLE.get((scene, tag))
        if dest:
            transition_to(dest)

    # ── NPC interact ──────────────────────────────────────────────────
    def handle_npc_interact():
        if not player:
            return
        all_npcs = npcs + lab_npcs
        for n in all_npcs:
            if n.in_range(player.cx, player.cy):
                line = n.next_dialogue()
                if line:
                    dialogue.start([(n.name, line)])
                    audio.play_sfx('blip')
                break

    # ── Proximity highlights ───────────────────────────────────────────
    def update_npc_highlights():
        if not player:
            return
        all_npcs = npcs + lab_npcs
        for n in all_npcs:
            n.highlight = n.in_range(player.cx, player.cy)

    # ── Draw gameplay ──────────────────────────────────────────────────
    def draw_gameplay(surf):
        if not active_map:
            return
        cam_x = active_map.camera.ix
        cam_y = active_map.camera.iy

        active_map.draw_bg(surf)

        # Draw all NPCs (street + lab)
        for n in (npcs + lab_npcs):
            n.draw(surf, cam_x, cam_y)

        # Draw player
        if player:
            player.draw(surf, cam_x, cam_y)

        active_map.draw_fg(surf)

        # Weather
        if rain:
            rain.draw(surf)

        # Particles
        psys.draw(surf)

        # HUD layer
        mission_box.draw(surf, W)
        hud.draw(surf, W, H)
        if dialogue.active:
            dialogue.draw(surf, W, H)
        if intro_card.active:
            intro_card.draw(surf, W, H)

        # Visual polish
        surf.blit(vignette,  (0, 0))
        surf.blit(scanlines, (0, 0))

        # Pause menu on top
        pause_menu.draw(surf, W, H)

    # ── Draw save notification ─────────────────────────────────────────
    _save_notif_t = [0.0]
    def draw_save_notif(surf):
        if _save_notif_t[0] > 0:
            a = min(255, int(_save_notif_t[0] * 400))
            ns_s = f_sm.render("◈ Game Saved", True, (0, 220, 180))
            nb   = pygame.Surface((ns_s.get_width() + 18, ns_s.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(nb, (5, 20, 50, min(220, a)), nb.get_rect(), border_radius=6)
            pygame.draw.rect(nb, (0, 180, 160, min(200, a)), nb.get_rect(), 1, border_radius=6)
            ns_s.set_alpha(a)
            nb.blit(ns_s, (9, 5))
            surf.blit(nb, (W - nb.get_width() - 12, H - nb.get_height() - 12))

    # ══════════════════════════════════════════════════════════════════
    # BOOT
    # ══════════════════════════════════════════════════════════════════
    _enter_scene(SC_INTRO)
    fade.set_black()
    fade.fade_in(350)

    # ══════════════════════════════════════════════════════════════════
    # MAIN LOOP
    # ══════════════════════════════════════════════════════════════════
    running = True
    while running:
        dt = min(clock.tick(FPS) / 1000.0, 0.05)

        # ── Event handling ────────────────────────────────────────────
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                k = event.key

                # --- Pause (ESC in gameplay) ---
                if k == pygame.K_ESCAPE:
                    if active_cut and hasattr(active_cut, 'handle_event'):
                        active_cut.handle_event(event)
                    elif scene in (SC_APT, SC_APT2, SC_VALORA, SC_ACADEMY,
                                   SC_LAB_DIAG, SC_SCHOOL, SC_STREETS):
                        if pause_menu.active:
                            pause_menu.close()
                            audio.play_sfx('cancel')
                        else:
                            pause_menu.open()
                            audio.play_sfx('select')

                # --- Pause menu navigation ---
                elif pause_menu.active:
                    result = pause_menu.key(k, audio)
                    if result == 'Resume':
                        pause_menu.close()
                        audio.play_sfx('confirm')
                    elif result == 'Save Game':
                        game_state['scene'] = scene
                        if player:
                            game_state['player_pos'] = [player.cx, player.cy]
                        if save_system.save(game_state):
                            audio.play_sfx('notify')
                            _save_notif_t[0] = 1.8
                    elif result == 'Load Game':
                        loaded = save_system.load()
                        if loaded:
                            game_state = loaded
                            pause_menu.close()
                            transition_to(loaded.get('scene', SC_TITLE))
                            audio.play_sfx('power')
                    elif result == 'Quit':
                        running = False

                # --- Interact / advance dialogue ---
                elif k in (pygame.K_e, pygame.K_z, pygame.K_RETURN):
                    if active_cut and hasattr(active_cut, 'handle_event'):
                        active_cut.handle_event(event)
                    elif dialogue.active:
                        dialogue.advance(audio)
                    elif scene in (SC_APT, SC_APT2, SC_VALORA,
                                   SC_ACADEMY, SC_SCHOOL, SC_STREETS):
                        handle_interact()
                        if not dialogue.active:
                            handle_npc_interact()
                    elif scene == SC_LAB_DIAG:
                        dialogue.advance(audio)

                # --- Any other key passed to active cutscene ---
                else:
                    if active_cut and hasattr(active_cut, 'handle_event'):
                        active_cut.handle_event(event)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if active_cut and hasattr(active_cut, 'handle_event'):
                    active_cut.handle_event(event)

        # ── Update ────────────────────────────────────────────────────
        if not pause_menu.active:

            fade.update(dt)
            mission_box.update(dt)
            hud.update(dt)
            intro_card.update(dt)
            psys.update(dt)
            dialogue.update(dt)
            if _save_notif_t[0] > 0:
                _save_notif_t[0] = max(0.0, _save_notif_t[0] - dt)

            if rain:
                rain.update(dt)

            if active_cut is not None:
                active_cut.update(dt)
                # Check if cutscene/minigame finished
                done_flag = getattr(active_cut, 'done', False)
                if done_flag and next_scene is None and not fade.busy:
                    _on_cutscene_done()

            elif active_map is not None:
                active_map.update(dt)

                if player and not dialogue.active:
                    player.update(dt, active_map.get_colliders())

                active_map.camera.follow(
                    player.cx if player else W // 2,
                    player.cy if player else H // 2,
                    dt
                )

                # Update all NPCs
                for n in (npcs + lab_npcs):
                    n.update(dt)

                update_npc_highlights()

        else:
            # Still update pause menu + fade even when paused
            pause_menu.update(dt)
            fade.update(dt)

        # ── Draw ─────────────────────────────────────────────────────
        screen.fill((0, 0, 0))

        if active_cut is not None:
            active_cut.draw(screen)

        elif active_map is not None:
            draw_gameplay(screen)

        else:
            screen.fill((3, 5, 18))

        # Fade overlay (always on top)
        fade.draw(screen, W, H)

        # Save notification
        draw_save_notif(screen)

        pygame.display.flip()

    # ── Shutdown ──────────────────────────────────────────────────────
    game_state['scene']    = scene
    game_state['playtime'] = game_state.get('playtime', 0.0) + pygame.time.get_ticks() / 1000.0
    save_system.save(game_state)
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()