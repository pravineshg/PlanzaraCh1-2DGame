"""
PLANZARA — battle.py  (Stock Market Minigame)
Valora Nexus Exchange — futuristic holographic trading.

CHANGES FROM v1:
  • Balance raised to 600 so player can buy immediately
  • NovaTech trend boosted → easy profit stock for new players
  • _trade_count tracks every BUY or SELL action
  • Game ends (is_done = True) after 5 trades and a 3-second completion pause
  • Tutorial panel guides player step-by-step until first trade
  • Progress bar "Trades X/5" always visible in header
  • Sell hints appear when owned stock's price has risen
  • Error messages now say WHAT to do, not just what went wrong
"""

import pygame, math, random

W, H = 960, 540
HIST_LEN = 90

STOCKS_DEF = [
    {'name': 'Skyline Robotics', 'short': 'SKRL', 'base': 142.5,
     'color': (0, 220, 180),  'trend':  0.30, 'vol': 6.0},
    # NovaTech is the "easy profit" stock — strong uptrend, low price
    {'name': 'NovaTech',         'short': 'NVTC', 'base': 89.2,
     'color': (80, 160, 255), 'trend':  0.55, 'vol': 3.5},
    {'name': 'Aether Energy',    'short': 'AETR', 'base': 215.8,
     'color': (255, 180, 0),  'trend': -0.20, 'vol': 11.0},
]

MITS_LINES = [
    ("Mits", "Okay… NovaTech is definitely going up."),
    ("Mits", "If this trade works, I'm upgrading my holo-console."),
    ("Mits", "5 trades done. Not bad for a morning session!"),   # shown on completion
]

TARGET_TRADES = 5


def _lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i]-a[i])*t) for i in range(3))


class StockMarketGame:
    """
    Futuristic stock-trading minigame.
    Call update(dt) and draw(surf) each frame.
    handle_event(event) for input.
    is_done becomes True after TARGET_TRADES transactions.
    """

    def __init__(self, fonts, audio=None):
        self.f_lg, self.f_md, self.f_sm, self.f_xs = fonts
        self.audio = audio
        self._done  = False
        self.t      = 0.0
        self.upd_t  = 0.0
        self.sel    = 1            # default: NovaTech (easy stock)
        self.balance = 600.0      # enough to buy NovaTech right away

        # ── trade tracking ──────────────────────────────────────────
        self._trade_count  = 0
        self._buy_prices   = {}    # short -> price paid (for profit calc)
        self._complete     = False
        self._complete_t   = 3.2   # seconds before auto-exit after completion

        self.msg   = "Welcome!  Select NovaTech (blue) and press  Z  to BUY."
        self.msg_t = 6.0

        # dialogue
        self.dlg_idx   = 0          # show hint 0 right away
        self.dlg_t     = 5.0
        self.dlg_shown = [False]*len(MITS_LINES)
        self.dlg_shown[0] = True    # fire immediately

        self._btn_hover    = [-1, -1]
        self.scan_lines_surf = self._make_scanlines()
        self._show_tutorial = True  # hide after first trade

        # Build stock state
        self.stocks = []
        for d in STOCKS_DEF:
            st = {**d}
            st['price']   = d['base']
            st['history'] = [d['base']] * HIST_LEN
            st['owned']   = 0
            self.stocks.append(st)

        self._grid = self._make_grid()

    # ── static helpers ────────────────────────────────────────────────

    def _make_grid(self):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        for x in range(0, W, 48):
            pygame.draw.line(s, (0, 90, 180, 12), (x, 0), (x, H))
        for y in range(0, H, 36):
            pygame.draw.line(s, (0, 90, 180, 10), (0, y), (W, y))
        return s

    def _make_scanlines(self):
        s = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(0, H, 3):
            pygame.draw.line(s, (0, 0, 0, 18), (0, y), (W, y))
        return s

    # ── price simulation ──────────────────────────────────────────────

    def _tick_prices(self):
        for s in self.stocks:
            drift = s['trend'] * 0.003
            shock = random.gauss(0, s['vol'] * 0.008)
            s['price'] = max(1.0, s['price'] * (1 + drift + shock))
            s['history'].append(s['price'])
            if len(s['history']) > HIST_LEN:
                s['history'].pop(0)

    # ── public API ────────────────────────────────────────────────────

    @property
    def is_done(self):
        return self._done

    @property
    def done(self):          # main.py checks .done — this was the stuck-screen bug
        return self._done

    def update(self, dt):
        if self._done:
            return
        self.t     += dt
        self.upd_t += dt
        if self.upd_t >= 0.22:
            self.upd_t = 0.0
            self._tick_prices()

        # message decay
        if self.msg_t > 0:
            self.msg_t -= dt
            if self.msg_t <= 0:
                self.msg = ''

        # dialogue decay
        if self.dlg_t > 0:
            self.dlg_t -= dt
            if self.dlg_t <= 0:
                self.dlg_idx = -1

        # timed hint lines (only if not yet shown)
        if not self.dlg_shown[1] and self.t > 5.0:
            self.dlg_shown[1] = True
            self.dlg_idx = 1
            self.dlg_t   = 4.5

        # completion auto-exit countdown
        if self._complete:
            self._complete_t -= dt
            if self._complete_t <= 0:
                self._done = True

    def handle_event(self, event):
        if self._done:
            return
        au = self.audio
        if event.type == pygame.KEYDOWN:
            k = event.key
            if k in (pygame.K_LEFT, pygame.K_a):
                self.sel = (self.sel - 1) % len(self.stocks)
                if au: au.play_sfx('blip')
            elif k in (pygame.K_RIGHT, pygame.K_d):
                self.sel = (self.sel + 1) % len(self.stocks)
                if au: au.play_sfx('blip')
            elif k in (pygame.K_z, pygame.K_e, pygame.K_RETURN):
                self._buy()
            elif k == pygame.K_x:
                self._sell()
            elif k == pygame.K_SPACE:
                if self.dlg_idx >= 0:
                    self.dlg_idx = -1; self.dlg_t = 0.0
                elif self._complete:
                    self._done = True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_click(*event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_hover(*event.pos)

    def _handle_mouse_hover(self, mx, my):
        self._btn_hover = [-1, -1]
        pw = (W - 60) // 3
        for i in range(len(self.stocks)):
            x    = 20 + i * (pw + 10)
            bw   = pw // 2 - 5
            by2  = 70 + (H - 190) + 8
            if pygame.Rect(x,           by2, bw, 34).collidepoint(mx, my):
                self._btn_hover = [i, 0]
            elif pygame.Rect(x+pw//2+5, by2, bw, 34).collidepoint(mx, my):
                self._btn_hover = [i, 1]

    def _handle_mouse_click(self, mx, my):
        pw = (W - 60) // 3
        for i in range(len(self.stocks)):
            x   = 20 + i * (pw + 10)
            bw  = pw // 2 - 5
            by2 = 70 + (H - 190) + 8
            if pygame.Rect(x,           by2, bw, 34).collidepoint(mx, my):
                self.sel = i; self._buy(); return
            if pygame.Rect(x+pw//2+5,   by2, bw, 34).collidepoint(mx, my):
                self.sel = i; self._sell(); return
        if self._complete and pygame.Rect(W//2-90, H//2+50, 180, 38).collidepoint(mx, my):
            self._done = True

    # ── trade actions ─────────────────────────────────────────────────

    def _buy(self):
        s = self.stocks[self.sel]
        if self._complete:
            return
        if self.balance >= s['price']:
            self.balance         -= s['price']
            s['owned']           += 1
            self._buy_prices[s['short']] = s['price']
            self._trade_count    += 1
            self._show_tutorial  = False
            remaining = TARGET_TRADES - self._trade_count
            if remaining > 0:
                self.msg   = (f"✓ Bought {s['short']} @ ◈{s['price']:.2f}"
                              f"  —  {remaining} trade(s) left")
            else:
                self.msg   = f"✓ Bought {s['short']} @ ◈{s['price']:.2f}"
            self.msg_t = 2.5
            if self.audio: self.audio.play_sfx('confirm')
            self._check_complete()
        else:
            self.msg   = (f"Not enough credits!  "
                          f"NovaTech (◈{self.stocks[1]['price']:.0f}) is cheapest.")
            self.msg_t = 2.2
            if self.audio: self.audio.play_sfx('cancel')

    def _sell(self):
        s = self.stocks[self.sel]
        if self._complete:
            return
        if s['owned'] > 0:
            buy_p  = self._buy_prices.get(s['short'], s['price'])
            profit = s['price'] - buy_p
            self.balance      += s['price']
            s['owned']        -= 1
            self._trade_count += 1
            sign = '+' if profit >= 0 else ''
            remaining = TARGET_TRADES - self._trade_count
            if remaining > 0:
                self.msg = (f"✓ Sold {s['short']} @ ◈{s['price']:.2f}  "
                            f"Profit: {sign}◈{profit:.2f}  —  {remaining} left")
            else:
                self.msg = (f"✓ Sold {s['short']} @ ◈{s['price']:.2f}  "
                            f"Profit: {sign}◈{profit:.2f}")
            self.msg_t = 2.5
            if self.audio: self.audio.play_sfx('confirm')
            self._check_complete()
        else:
            self.msg   = f"You don't own {s['short']}!  Press  Z  to BUY first."
            self.msg_t = 2.2
            if self.audio: self.audio.play_sfx('cancel')

    def _check_complete(self):
        if self._trade_count >= TARGET_TRADES and not self._complete:
            self._complete   = True
            self._complete_t = 3.2
            self.msg         = f"Session complete!  Final balance: ◈{self.balance:.1f}"
            self.msg_t       = 3.5
            self.dlg_idx     = 2
            self.dlg_t       = 5.0
            if self.audio: self.audio.play_sfx('power')

    # ── drawing ───────────────────────────────────────────────────────

    def draw(self, surf):
        surf.fill((3, 7, 26))
        surf.blit(self._grid, (0, 0))

        # corner glow pulses
        for cx2, cy2, col in [(0,0,(0,60,120)),(W,0,(0,80,160)),
                               (0,H,(0,40,100)),(W,H,(0,60,120))]:
            gs = pygame.Surface((200,200), pygame.SRCALPHA)
            r  = int(80 + math.sin(self.t*0.8)*20)
            pygame.draw.circle(gs, (*col, 30), (100,100), r)
            surf.blit(gs, (cx2-100, cy2-100), special_flags=pygame.BLEND_RGBA_ADD)

        self._draw_header(surf)
        self._draw_panels(surf)
        self._draw_sell_hints(surf)

        if self._show_tutorial:
            self._draw_tutorial(surf)

        self._draw_message(surf)
        self._draw_dialogue(surf)
        self._draw_controls(surf)

        if self._complete:
            self._draw_completion(surf)

        surf.blit(self.scan_lines_surf, (0, 0))

    # ── sub-draw helpers ──────────────────────────────────────────────

    def _draw_header(self, surf):
        hdr = pygame.Surface((W, 62), pygame.SRCALPHA)
        pygame.draw.rect(hdr, (4, 12, 52, 240), (0, 0, W, 62))
        pygame.draw.rect(hdr, (0, 180, 255, 120), (0, 60, W, 2))

        ts = self.f_lg.render("◈  VALORA NEXUS EXCHANGE  ◈", True, (0, 220, 255))
        hdr.blit(ts, (W//2 - ts.get_width()//2, 10))

        # balance
        bal_col = (0, 255, 180) if self.balance >= 100 else (255, 100, 80)
        bs2 = self.f_sm.render(f"◈ {self.balance:.1f}", True, bal_col)
        hdr.blit(bs2, (W - bs2.get_width() - 18, 18))

        # ── trade progress bar ──────────────────────────────────────
        done  = min(self._trade_count, TARGET_TRADES)
        bar_w = 180
        bar_x = W - bs2.get_width() - 18 - bar_w - 20
        bar_y = 14
        # label
        lbl = self.f_xs.render(f"Trades {done}/{TARGET_TRADES}", True, (0, 180, 255))
        hdr.blit(lbl, (bar_x, bar_y - 1))
        # track
        pygame.draw.rect(hdr, (10, 25, 68), (bar_x, bar_y+16, bar_w, 10), border_radius=5)
        pygame.draw.rect(hdr, (0, 80, 160), (bar_x, bar_y+16, bar_w, 10), 1, border_radius=5)
        # fill
        fill = int(bar_w * done / TARGET_TRADES)
        if fill > 0:
            fc = (0, 220, 130) if done < TARGET_TRADES else (0, 255, 80)
            pygame.draw.rect(hdr, fc, (bar_x, bar_y+16, fill, 10), border_radius=5)
        # pip markers
        for i in range(1, TARGET_TRADES):
            px2 = bar_x + int(bar_w * i / TARGET_TRADES)
            pygame.draw.line(hdr, (0, 40, 90), (px2, bar_y+16), (px2, bar_y+26))

        surf.blit(hdr, (0, 0))

    def _draw_panels(self, surf):
        pw = (W - 60) // 3
        ph = H - 190
        for i, s in enumerate(self.stocks):
            x   = 20 + i * (pw + 10)
            y   = 66
            sel = (i == self.sel)
            p   = pygame.Surface((pw, ph), pygame.SRCALPHA)

            bg = (10, 22, 68, 230) if sel else (6, 14, 48, 200)
            pygame.draw.rect(p, bg, (0, 0, pw, ph), border_radius=10)
            bcol = (*s['color'], 240 if sel else 90)
            pygame.draw.rect(p, bcol, (0, 0, pw, ph), 2 if sel else 1, border_radius=10)
            if sel:
                pygame.draw.rect(p, (*s['color'], 255), (0, 0, 4, ph), border_radius=4)

            ns = self.f_sm.render(s['name'], True, s['color'])
            ts = self.f_xs.render(s['short'], True, s['color'])
            p.blit(ns, (12, 10))
            p.blit(ts, (pw - ts.get_width() - 12, 12))

            hist = s['history']
            up   = len(hist) < 2 or hist[-1] >= hist[-2]
            pcol = (0, 255, 120) if up else (255, 80, 80)
            arrow = "▲" if up else "▼"
            ps2  = self.f_md.render(f"{arrow} ◈{s['price']:.2f}", True, pcol)
            p.blit(ps2, (12, 32))

            if len(hist) >= 10:
                chg  = (s['price'] - hist[-10]) / max(hist[-10], 0.01) * 100
                ccol = (0, 255, 120) if chg >= 0 else (255, 80, 80)
                cs2  = self.f_xs.render(f"{'▲' if chg>=0 else '▼'}{abs(chg):.2f}%",
                                        True, ccol)
                p.blit(cs2, (pw - cs2.get_width() - 12, 36))

            ow = self.f_xs.render(f"Owned: {s['owned']}", True, (140,175,220))
            p.blit(ow, (12, 57))

            # show cost hint when player owns none
            if s['owned'] == 0:
                ch2 = self.f_xs.render(f"Cost: ◈{s['price']:.0f}", True, (80,120,170))
                p.blit(ch2, (pw - ch2.get_width() - 12, 57))

            gx, gy2, gw2, gh = 10, 76, pw-20, ph-100
            pygame.draw.rect(p, (2, 6, 28, 200), (gx, gy2, gw2, gh), border_radius=4)
            pygame.draw.rect(p, (*s['color'][:3], 45), (gx, gy2, gw2, gh), 1, border_radius=4)
            self._draw_graph(p, hist, gx, gy2, gw2, gh, s['color'])

            surf.blit(p, (x, y))

            # BUY / SELL buttons
            bw3   = pw // 2 - 5
            btn_y = y + ph + 8
            can_buy  = self.balance >= s['price']
            can_sell = s['owned'] > 0

            for bi, (label, rx, bcol2, fc, enabled) in enumerate([
                ("BUY  [Z]",  x,           (0,  70, 35), (0, 255, 140), can_buy),
                ("SELL [X]",  x+pw//2+5,   (70, 18, 18), (255, 100,100), can_sell),
            ]):
                br = pygame.Rect(rx, btn_y, bw3, 34)
                hover = (self._btn_hover == [i, bi])
                dim   = 100 if not enabled else 255
                hcol  = tuple(min(255, c+40) for c in bcol2)
                dc    = tuple(c * dim // 255 for c in (hcol if hover else bcol2))
                pygame.draw.rect(surf, dc, br, border_radius=7)
                fc2   = tuple(c * dim // 255 for c in fc)
                pygame.draw.rect(surf, fc2, br, 1, border_radius=7)
                if hover and enabled:
                    gs = pygame.Surface((bw3+8,42), pygame.SRCALPHA)
                    pygame.draw.rect(gs, (*fc, 30), gs.get_rect(), border_radius=7)
                    surf.blit(gs, (br.x-4, br.y-4), special_flags=pygame.BLEND_RGBA_ADD)
                ft = self.f_xs.render(label, True, fc2)
                surf.blit(ft, (br.x + br.w//2 - ft.get_width()//2, br.y + 10))

    def _draw_sell_hints(self, surf):
        """Show a glowing ▲ SELL hint above stock panel when owned price has risen."""
        pw = (W - 60) // 3
        for i, s in enumerate(self.stocks):
            if s['owned'] <= 0:
                continue
            buy_p = self._buy_prices.get(s['short'], s['price'])
            if s['price'] > buy_p * 1.02:   # at least 2% up
                profit = s['price'] - buy_p
                x  = 20 + i * (pw + 10)
                y  = 66 + (H - 190) - 28
                pulse = int(180 + math.sin(self.t * 4) * 75)
                hint_col = (0, pulse, 100)
                ht = self.f_xs.render(
                    f"▲ +◈{profit:.2f}  SELL for profit! [X]", True, hint_col)
                bg = pygame.Surface((ht.get_width()+16, ht.get_height()+8), pygame.SRCALPHA)
                pygame.draw.rect(bg, (0, 40, 20, 180), bg.get_rect(), border_radius=5)
                pygame.draw.rect(bg, (*hint_col, 200), bg.get_rect(), 1, border_radius=5)
                bg.blit(ht, (8, 4))
                surf.blit(bg, (x + pw//2 - bg.get_width()//2, y))

    def _draw_tutorial(self, surf):
        """Step-by-step guide shown until the first trade is made."""
        bx, by2 = W//2 - 240, H - 170
        box = pygame.Surface((480, 72), pygame.SRCALPHA)
        pygame.draw.rect(box, (4, 16, 60, 230), box.get_rect(), border_radius=10)
        pygame.draw.rect(box, (0, 200, 255, 180), box.get_rect(), 2, border_radius=10)
        # blinking border pulse
        pulse = int(120 + math.sin(self.t * 3) * 80)
        pygame.draw.rect(box, (0, pulse, 255, 80), box.get_rect(), 1, border_radius=10)

        head = self.f_sm.render("◈  HOW TO TRADE", True, (0, 220, 255))
        box.blit(head, (12, 6))

        step1 = self.f_xs.render(
            "1.  ◄ ► or A/D keys to select stock    |    Z or click BUY to buy",
            True, (140, 200, 255))
        step2 = self.f_xs.render(
            "2.  Wait for price to rise ▲             |    X or click SELL to sell for profit",
            True, (100, 230, 160))
        goal  = self.f_xs.render(
            f"GOAL: make {TARGET_TRADES} trades  (BUYs + SELLs)  →  NovaTech is trending UP!",
            True, (255, 220, 80))
        box.blit(step1, (12, 26))
        box.blit(step2, (12, 42))
        box.blit(goal,  (12, 56))
        surf.blit(box, (bx, by2))

    def _draw_graph(self, surf, hist, gx, gy, gw, gh, color):
        if len(hist) < 2:
            return
        mn  = min(hist); mx2 = max(hist)
        rng = max(mx2 - mn, 1.0)
        pts = []
        for j, v in enumerate(hist):
            px2 = gx + 4 + int(j / (len(hist)-1) * (gw-8))
            py2 = gy + gh - 4 - int((v - mn) / rng * (gh-8))
            pts.append((px2, py2))
        fs = pygame.Surface((gw, gh), pygame.SRCALPHA)
        fill = [(pts[0][0]-gx, gh)] + [(p[0]-gx, p[1]-gy) for p in pts] + [(pts[-1][0]-gx, gh)]
        pygame.draw.polygon(fs, (*color[:3], 22), fill)
        surf.blit(fs, (gx, gy))
        pygame.draw.lines(surf, color, False, pts, 2)
        last = pts[-1]
        pg2 = pygame.Surface((14,14), pygame.SRCALPHA)
        pygame.draw.circle(pg2, (*color[:3], 80), (7,7), 7)
        pygame.draw.circle(pg2, (255,255,255,200), (7,7), 3)
        surf.blit(pg2, (last[0]-7, last[1]-7))

    def _draw_message(self, surf):
        if not self.msg or self.msg_t <= 0:
            return
        alpha = min(255, int(self.msg_t * 180))
        ms    = self.f_sm.render(self.msg, True, (255, 220, 80))
        bx2   = W//2 - ms.get_width()//2 - 14
        by2   = H//2 - 30
        bg    = pygame.Surface((ms.get_width()+28, ms.get_height()+14), pygame.SRCALPHA)
        pygame.draw.rect(bg, (18, 24, 58, min(alpha, 210)), bg.get_rect(), border_radius=8)
        pygame.draw.rect(bg, (0, 180, 255, min(alpha, 160)), bg.get_rect(), 1, border_radius=8)
        bg.blit(ms, (14, 7))
        surf.blit(bg, (bx2, by2))

    def _draw_dialogue(self, surf):
        if self.dlg_idx < 0 or self.dlg_idx >= len(MITS_LINES):
            return
        spk, txt = MITS_LINES[self.dlg_idx]
        box = pygame.Surface((520, 68), pygame.SRCALPHA)
        pygame.draw.rect(box, (5, 12, 48, 215), box.get_rect(), border_radius=9)
        pygame.draw.rect(box, (0, 155, 255, 160), box.get_rect(), 1, border_radius=9)
        pygame.draw.rect(box, (0, 155, 255, 220), (0, 0, 4, 68), border_radius=4)
        sn = self.f_xs.render(f"● {spk}", True, (0, 210, 255))
        st = self.f_sm.render(txt, True, (200, 220, 255))
        hint = self.f_xs.render("SPACE: dismiss", True, (70, 100, 160))
        box.blit(sn, (12, 8)); box.blit(st, (12, 30))
        box.blit(hint, (box.get_width() - hint.get_width() - 10, 50))
        surf.blit(box, (W//2 - 260, H - 170))

    def _draw_controls(self, surf):
        cs = self.f_xs.render(
            "◄► / A D : Select  │  Z / Click : BUY  │  X : SELL  │  SPACE: dismiss hint",
            True, (70, 105, 165))
        surf.blit(cs, (W//2 - cs.get_width()//2, H - 24))

    def _draw_completion(self, surf):
        """Full-screen overlay shown when all trades are complete."""
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 160))
        surf.blit(ov, (0, 0))

        bw2, bh2 = 420, 160
        bx2 = W//2 - bw2//2; by2 = H//2 - bh2//2
        box = pygame.Surface((bw2, bh2), pygame.SRCALPHA)
        pygame.draw.rect(box, (4, 18, 60, 240), box.get_rect(), border_radius=14)
        pulse = int(160 + math.sin(self.t * 4) * 95)
        pygame.draw.rect(box, (0, pulse, 130, 220), box.get_rect(), 3, border_radius=14)

        done_t = self.f_lg.render("✓  TRADES COMPLETE", True, (0, 255, 140))
        bal_t  = self.f_md.render(f"Final Balance:  ◈ {self.balance:.1f}", True, (255,220,80))
        cont_t = self.f_sm.render("Continue  ▶  (SPACE or click)", True, (80, 170, 255))

        box.blit(done_t, (bw2//2 - done_t.get_width()//2, 18))
        box.blit(bal_t,  (bw2//2 - bal_t.get_width()//2,  62))
        box.blit(cont_t, (bw2//2 - cont_t.get_width()//2, 108))
        surf.blit(box, (bx2, by2))