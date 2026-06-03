import pygame, math, random

W, H = 960, 540
TILE = 48

# ══════════════════════════════════════════════════════════════════════
# Camera
# ══════════════════════════════════════════════════════════════════════
class Camera:
    def __init__(self, map_w, map_h):
        self.x = 0.0; self.y = 0.0
        self.map_w = map_w; self.map_h = map_h
    def follow(self, cx, cy, dt, speed=7.0):
        tx = cx - W//2; ty = cy - H//2
        self.x += (tx - self.x) * min(1.0, dt * speed)
        self.y += (ty - self.y) * min(1.0, dt * speed)
        self.clamp()
    def snap(self, cx, cy):
        self.x = cx - W//2; self.y = cy - H//2; self.clamp()
    def clamp(self):
        self.x = max(0, min(self.x, max(0, self.map_w - W)))
        self.y = max(0, min(self.y, max(0, self.map_h - H)))
    @property
    def ix(self): return int(self.x)
    @property
    def iy(self): return int(self.y)

# ══════════════════════════════════════════════════════════════════════
# Tile helpers
# ══════════════════════════════════════════════════════════════════════
def _floor_futuristic(size=TILE):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((18, 22, 52))
    pygame.draw.rect(s, (24, 30, 68), (2, 2, size-4, size-4), border_radius=3)
    pygame.draw.rect(s, (0, 80, 160, 40), (1, 1, size-2, size-2), 1, border_radius=3)
    c = size // 2
    pygame.draw.line(s, (0, 100, 180, 60), (c, 4), (c, size-4), 1)
    pygame.draw.line(s, (0, 100, 180, 60), (4, c), (size-4, c), 1)
    return s

def _floor_2026(size=TILE):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((72, 72, 72))
    pygame.draw.rect(s, (82, 82, 82), (2, 2, size-4, size-4), border_radius=2)
    pygame.draw.rect(s, (55, 55, 55), (1, 1, size-2, size-2), 1)
    return s

def _floor_wood(size=TILE):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((140, 95, 55))
    for i in range(0, size, 8):
        pygame.draw.line(s, (120, 80, 42), (0, i), (size, i+2), 1)
    pygame.draw.rect(s, (160, 110, 65), (2, 2, size-4, size-4), border_radius=2)
    pygame.draw.rect(s, (100, 65, 35), (1, 1, size-2, size-2), 1)
    return s

def _road(size=TILE):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    s.fill((28, 28, 38))
    pygame.draw.rect(s, (35, 35, 50), (2, 2, size-4, size-4), border_radius=2)
    return s

# ══════════════════════════════════════════════════════════════════════
# Base Map
# ══════════════════════════════════════════════════════════════════════
class GameMap:
    def __init__(self, name, width, height):
        self.name = name; self.width = width; self.height = height
        self.camera = Camera(width, height)
        self._colliders = []
        self._interact_zones = []   # (rect, tag) — E key
        self._trigger_zones  = []   # (rect, tag) — auto proximity
        self._t = 0.0
    def update(self, dt): self._t += dt
    def get_colliders(self): return self._colliders
    def get_interact_zones(self): return self._interact_zones
    def get_trigger_zones(self): return self._trigger_zones
    def _check_interact(self, px, py):
        for rect, tag in self._interact_zones:
            if rect.collidepoint(px, py): return tag
        return None
    def _check_trigger(self, px, py):
        for rect, tag in self._trigger_zones:
            if rect.collidepoint(px, py): return tag
        return None
    def draw_bg(self, surf): pass
    def draw_fg(self, surf): pass

# ══════════════════════════════════════════════════════════════════════
# APARTMENT MAP  ── BIG FIX: visible centred exit door + trigger zone
# ══════════════════════════════════════════════════════════════════════
class ApartmentMap(GameMap):
    def __init__(self):
        super().__init__('apartment', 640, 480)
        self._floor = _floor_futuristic(TILE)

        # ── Interact zones (E key) ─────────────────────────────────
        self._interact_zones = [
            (pygame.Rect(310, 130, 130, 110), 'terminal'),   # stock terminal
            (pygame.Rect(220, 390, 200, 90),  'door'),       # exit door — bottom centre
        ]

        # ── Auto-proximity trigger zones (walk into = auto-transition)
        self._trigger_zones = [
            (pygame.Rect(220, 410, 200, 70), 'door'),        # same as door but walk-through
        ]

        # ── Colliders — bottom wall has a GAP in the centre for the door
        self._colliders = [
            pygame.Rect(0,   0,   640,  48),    # top wall
            pygame.Rect(0,   0,    48, 480),    # left wall
            pygame.Rect(592, 0,    48, 480),    # right wall
            # Bottom wall — split into two segments leaving door gap (x 220–420)
            pygame.Rect(0,   430, 220,  50),    # bottom-left segment
            pygame.Rect(420, 430, 220,  50),    # bottom-right segment
            # Furniture
            pygame.Rect(310,  80, 210, 100),    # terminal desk
            pygame.Rect(80,   80, 160,  80),    # couch
            pygame.Rect(80,  200, 120, 100),    # shelf
        ]
        self._particles = []

    def update(self, dt):
        super().update(dt)
        if random.random() < 0.25:
            self._particles.append({
                'x': random.uniform(60, 580), 'y': random.uniform(60, 420),
                'vy': random.uniform(-12, -28), 'vx': random.uniform(-4, 4),
                'life': random.uniform(1.5, 3.5), 'max': 3.5,
                'col': random.choice([(0,180,255),(0,255,200),(100,150,255)])
            })
        self._particles = [p for p in self._particles if p['life'] > 0]
        for p in self._particles:
            p['x'] += p['vx']*dt; p['y'] += p['vy']*dt; p['life'] -= dt

    def draw_bg(self, surf):
        cx, cy = self.camera.ix, self.camera.iy
        t = self._t

        # Floor tiles
        sx = -(cx % TILE); sy = -(cy % TILE)
        for fy in range(sy, H+TILE, TILE):
            for fx in range(sx, W+TILE, TILE):
                surf.blit(self._floor, (fx, fy))

        # Top wall
        pygame.draw.rect(surf, (12, 16, 44), (0-cx, 0-cy, 640, 48))
        pygame.draw.rect(surf, (0, 80, 160, 60), (0-cx, 46-cy, 640, 2))

        # Side walls
        pygame.draw.rect(surf, (14, 18, 50), (0-cx,   48-cy, 48, 384))
        pygame.draw.rect(surf, (14, 18, 50), (592-cx, 48-cy, 48, 384))

        # City window (left)
        self._draw_city_window(surf, 108-cx, 95-cy, 150, 130, t)

        # Terminal desk + monitor
        self._draw_terminal(surf, 315-cx, 85-cy, t)

        # Couch
        self._draw_couch(surf, 80-cx, 80-cy)

        # Shelf
        self._draw_shelf(surf, 80-cx, 200-cy)

        # Ambient particles
        for p in self._particles:
            r = 2; a = int(180 * p['life'] / p['max'])
            ps = pygame.Surface((r*2+4, r*2+4), pygame.SRCALPHA)
            pygame.draw.circle(ps, (*p['col'], a), (r+2,r+2), r+1)
            surf.blit(ps, (int(p['x']-cx-r-2), int(p['y']-cy-r-2)),
                      special_flags=pygame.BLEND_RGBA_ADD)

        # ══ EXIT DOOR — bottom centre, big, unmissable ══════════════
        self._draw_exit_door(surf, 220-cx, 400-cy, 200, 80, t)

    def _draw_exit_door(self, surf, x, y, dw, dh, t):
        """Prominent glowing exit door — cannot be missed."""
        # Outer glow
        glow_al = int(55 + math.sin(t * 2.0) * 30)
        g = pygame.Surface((dw+40, dh+40), pygame.SRCALPHA)
        pygame.draw.rect(g, (0, 200, 255, glow_al), g.get_rect(), border_radius=12)
        surf.blit(g, (x-20, y-20), special_flags=pygame.BLEND_RGBA_ADD)

        # Door frame
        pygame.draw.rect(surf, (6, 28, 80),  (x, y, dw, dh), border_radius=8)
        pygame.draw.rect(surf, (0, 200, 255), (x, y, dw, dh), 3, border_radius=8)

        # Two door panels
        ph = dh - 12
        pygame.draw.rect(surf, (10, 45, 120), (x+6,    y+6, dw//2-10, ph), border_radius=5)
        pygame.draw.rect(surf, (10, 45, 120), (x+dw//2+4, y+6, dw//2-10, ph), border_radius=5)
        pygame.draw.line(surf, (0, 160, 220), (x+dw//2, y+8), (x+dw//2, y+dh-8), 2)

        # Door handles
        for hx in [x+dw//2-14, x+dw//2+8]:
            pygame.draw.circle(surf, (0, 180, 255), (hx, y+dh//2), 5)
            pygame.draw.circle(surf, (0, 140, 200), (hx, y+dh//2), 5, 1)

        # "EXIT" label centred on door
        f_door = pygame.font.SysFont("consolas", 16, bold=True)
        lbl = f_door.render("▼  EXIT  ▼", True, (0, 230, 255))
        surf.blit(lbl, (x + dw//2 - lbl.get_width()//2, y + dh//2 - lbl.get_height()//2))

        # Bouncing down-arrows ABOVE the door to draw attention
        arr_bob = int(math.sin(t * 4.0) * 6)
        f_arr = pygame.font.SysFont("consolas", 20, bold=True)
        for i, offset in enumerate([0, 14]):
            a_al = max(0, int(200 - i * 70))
            arr = f_arr.render("▼", True, (0, 220, 255))
            arr.set_alpha(a_al)
            surf.blit(arr, (x + dw//2 - arr.get_width()//2, y - 48 + offset + arr_bob))

        # Pulsing [E] prompt below the door
        ep_al = int(160 + math.sin(t * 3.5) * 80)
        ep_bob = int(math.sin(t * 3.0) * 3)
        f_ep = pygame.font.SysFont("consolas", 13)
        ep = f_ep.render("[ E ]  Leave Apartment", True, (0, 210, 255))
        ep.set_alpha(ep_al)
        surf.blit(ep, (x + dw//2 - ep.get_width()//2, y + dh + 6 + ep_bob))

    def _draw_city_window(self, surf, x, y, w, h, t):
        ws = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(h):
            c = int(8 + i/h * 22)
            pygame.draw.line(ws, (c, c*2, c*6), (0, i), (w, i))
        bldgs = [(10,40,28,80,(0,40,100)),(48,20,22,100,(0,50,120)),
                 (80,50,30,70,(0,35,90)),(120,30,20,90,(0,45,110))]
        for bx,by2,bw2,bh2,bc in bldgs:
            pygame.draw.rect(ws, bc, (bx, h-bh2, bw2, bh2))
            for wy in range(h-bh2+6, h-6, 10):
                for wx in range(bx+4, bx+bw2-4, 8):
                    col = (0,200,255) if (wx+wy+int(t))%3!=0 else (0,80,160)
                    pygame.draw.rect(ws, col, (wx, wy, 4, 6))
        surf.blit(ws, (x, y))
        pygame.draw.rect(surf, (0, 120, 220), (x, y, w, h), 2)
        pygame.draw.rect(surf, (10, 20, 60), (x-4, y-4, w+8, 8))
        pygame.draw.rect(surf, (10, 20, 60), (x-4, y+h-4, w+8, 8))

    def _draw_terminal(self, surf, x, y, t):
        pygame.draw.rect(surf, (18, 24, 62), (x, y+44, 210, 60), border_radius=6)
        pygame.draw.rect(surf, (0, 100, 200), (x, y+44, 210, 60), 1, border_radius=6)
        pygame.draw.rect(surf, (5, 15, 50),   (x+20, y, 170, 84), border_radius=4)
        pygame.draw.rect(surf, (0, 180, 255), (x+20, y, 170, 84), 2, border_radius=4)
        pts = []
        for i in range(13):
            pts.append((x+28+i*12, y+42-int(math.sin(i*0.7+t*2)*14)))
        if len(pts) >= 2:
            pygame.draw.lines(surf, (0, 255, 180), False, pts, 2)
        gs = pygame.Surface((210, 104), pygame.SRCALPHA)
        a = int(38 + math.sin(t*2)*14)
        pygame.draw.rect(gs, (0, 180, 255, a), gs.get_rect(), border_radius=6)
        surf.blit(gs, (x+16, y-4), special_flags=pygame.BLEND_RGBA_ADD)
        ep = int(120 + math.sin(t*3)*60)
        es = pygame.font.SysFont("consolas", 13).render("[E] Check Market", True, (0,200,255))
        es.set_alpha(ep)
        surf.blit(es, (x+105-es.get_width()//2, y+100))

    def _draw_couch(self, surf, x, y):
        pygame.draw.rect(surf, (25,35,80), (x,y+20,160,60), border_radius=8)
        pygame.draw.rect(surf, (35,50,110), (x+8,y+20,144,50), border_radius=6)
        pygame.draw.rect(surf, (0,100,200), (x,y+20,160,60), 1, border_radius=8)
        for i in range(3):
            pygame.draw.rect(surf, (30,45,105), (x+10+i*50,y+28,40,36), border_radius=6)

    def _draw_shelf(self, surf, x, y):
        pygame.draw.rect(surf, (18,24,62), (x,y+80,120,20), border_radius=3)
        pygame.draw.rect(surf, (0,100,200), (x,y+80,120,20), 1, border_radius=3)
        for i,c in enumerate([(255,80,80),(80,200,255),(255,200,0)]):
            pygame.draw.rect(surf, c, (x+10+i*38,y+60,22,20), border_radius=3)

    def draw_fg(self, surf): pass

# ══════════════════════════════════════════════════════════════════════
# VALORA CITY STREET
# ══════════════════════════════════════════════════════════════════════
class ValoraStreetMap(GameMap):
    def __init__(self):
        super().__init__('valora', 1440, 720)
        self._road_tile  = _road(TILE)
        self._floor_tile = _floor_futuristic(TILE)
        self._vehicles = []; self._holo_ads = []
        self._init_traffic(); self._init_ads()
        self._colliders = [
            pygame.Rect(0,0,1440,96), pygame.Rect(0,0,80,720),
            pygame.Rect(1360,0,80,720), pygame.Rect(0,624,1440,96),
            pygame.Rect(100,100,260,300), pygame.Rect(400,100,200,240),
            pygame.Rect(640,100,180,220), pygame.Rect(860,100,220,260),
            pygame.Rect(1120,100,220,280), pygame.Rect(1100,580,260,44),
        ]
        self._interact_zones = [
            (pygame.Rect(80, 545, 120, 75), 'scooty'),
            (pygame.Rect(1100, 525, 260, 99), 'academy_gate'),
        ]
        self._trigger_zones = [
            (pygame.Rect(80,  545, 120, 75),  'scooty'),
            (pygame.Rect(1100,525, 260, 99), 'academy_gate'),
        ]

    def _init_traffic(self):
        for lane in [380,430,470]:
            for _ in range(3):
                self._vehicles.append({
                    'x': random.randint(0,1440), 'y': lane,
                    'speed': random.uniform(180,340), 'dir': random.choice([1,-1]),
                    'color': random.choice([(0,200,255),(255,100,80),(200,255,100),(255,200,0)]),
                    'w': random.randint(64,90), 'h': 26,
                    'glow': random.uniform(0.5,1.5),
                })

    def _init_ads(self):
        for i,x in enumerate([120,420,700,900,1150]):
            self._holo_ads.append({
                'x':x,'y':108,'w':140,'h':90,
                'text':['NEXUSOIL▶','SKYLINK∞','AETHER⚡','VOLTEX◈','OMNI∇'][i%5],
                'col':[(0,220,255),(255,80,200),(80,255,160),(255,220,0),(0,200,255)][i%5],
                'phase':random.uniform(0,6),
            })

    def update(self, dt):
        super().update(dt)
        for v in self._vehicles:
            v['x'] += v['speed']*v['dir']*dt
            if v['dir']==1 and v['x']>1500: v['x']=-100
            elif v['dir']==-1 and v['x']<-100: v['x']=1500

    def draw_bg(self, surf):
        cx,cy=self.camera.ix,self.camera.iy; t=self._t
        for i in range(H):
            rr=int(3+i/H*10); gg=int(4+i/H*10); bb=int(18+i/H*28)
            pygame.draw.line(surf,(rr,gg,bb),(0,i),(W,i))
        self._draw_skyline(surf, cx*0.3, cy, t)
        road_y=360-cy
        pygame.draw.rect(surf,(22,22,34),(0,road_y,W,160))
        for lane_y in [380,430]:
            ly=lane_y-cy
            for x in range(-(cx%80),W,80):
                pygame.draw.rect(surf,(60,60,80),(x,ly,40,4))
        pygame.draw.rect(surf,(22,28,58),(0,320-cy,W,40))
        pygame.draw.rect(surf,(0,120,200,60),(0,358-cy,W,2))
        for bx,bw,bh in [(100,260,280),(400,200,220),(640,180,200),(860,220,240),(1120,220,260)]:
            self._draw_building(surf,bx-cx,100-cy,bw,bh,t)
        for ad in self._holo_ads:
            self._draw_holo_ad(surf,ad['x']-cx,ad['y']-cy,ad,t)
        for v in self._vehicles:
            self._draw_vehicle(surf,int(v['x']-cx),v['y']-cy,v,t)
        self._draw_academy_gate(surf,1100-cx,490-cy,t)
        self._draw_scooty(surf,100-cx,530-cy,t)

    def _draw_skyline(self,surf,cx,cy,t):
        bdata=[(0,80,80,300),(90,120,60,260),(160,60,100,320),(270,90,70,280),
               (350,50,90,330),(450,100,80,270),(540,70,110,310),(660,80,90,290),
               (760,55,100,330),(870,90,80,270),(960,65,95,300),(1060,80,110,280),
               (1180,50,90,320),(1280,85,80,270)]
        for bx,by,bw2,bh2 in bdata:
            sx=int(bx-cx); sy=H-bh2-50
            pygame.draw.rect(surf,(6,10,35),(sx,sy,bw2,bh2))
            for wy in range(sy+8,sy+bh2-8,12):
                for wx in range(sx+6,sx+bw2-6,10):
                    a=int(40+math.sin(t*0.5+wx*0.1+wy*0.1)*20)
                    if a>0:
                        ws=pygame.Surface((5,7),pygame.SRCALPHA)
                        ws.fill((0,160,255,max(0,a))); surf.blit(ws,(wx,wy))

    def _draw_building(self,surf,x,y,w,h,t):
        if x+w<0 or x>W: return
        pygame.draw.rect(surf,(14,20,58),(x,y,w,h),border_radius=4)
        pygame.draw.rect(surf,(22,32,80),(x+4,y+4,w-8,h-8),border_radius=3)
        pygame.draw.rect(surf,(8,50,120,80),(x+8,y+8,w-16,h-20),border_radius=2)
        for wy in range(y+12,y+h-16,20):
            for wx in range(x+12,x+w-12,16):
                phase=(wx+wy+int(t*0.5))%5
                col=(0,180,255) if phase!=0 else (0,50,120)
                ws=pygame.Surface((10,14),pygame.SRCALPHA); ws.fill((*col,180))
                surf.blit(ws,(wx,wy))
        a=int(100+math.sin(t*1.2+x*0.01)*40)
        pygame.draw.rect(surf,(0,200,255,a),(x,y,w,h),1,border_radius=4)

    def _draw_holo_ad(self,surf,x,y,ad,t):
        if x+ad['w']<0 or x>W: return
        a=int(140+math.sin(t*2+ad['phase'])*40)
        hs=pygame.Surface((ad['w'],ad['h']),pygame.SRCALPHA)
        pygame.draw.rect(hs,(*ad['col'][:3],a//4),hs.get_rect(),border_radius=4)
        pygame.draw.rect(hs,(*ad['col'][:3],min(255,a)),hs.get_rect(),1,border_radius=4)
        fs=pygame.font.SysFont("consolas",13,bold=True)
        ts=fs.render(ad['text'],True,ad['col']); ts.set_alpha(a)
        hs.blit(ts,(ad['w']//2-ts.get_width()//2,ad['h']//2-ts.get_height()//2))
        surf.blit(hs,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_vehicle(self,surf,x,y,v,t):
        if x+v['w']<0 or x>W: return
        vy=y-v['h']//2
        pygame.draw.rect(surf,(20,25,55),(x,vy,v['w'],v['h']),border_radius=6)
        pygame.draw.rect(surf,v['color'],(x,vy,v['w'],v['h']),1,border_radius=6)
        gs=pygame.Surface((v['w'],10),pygame.SRCALPHA)
        a2=int(60+math.sin(t*3)*20)
        pygame.draw.ellipse(gs,(*v['color'][:3],a2),gs.get_rect())
        surf.blit(gs,(x,vy+v['h']),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_academy_gate(self,surf,x,y,t):
        for px2 in [x,x+220]:
            pygame.draw.rect(surf,(18,28,72),(px2,y,30,90),border_radius=3)
            pygame.draw.rect(surf,(0,180,255),(px2,y,30,90),1,border_radius=3)
            a=int(100+math.sin(t*2)*40)
            gs=pygame.Surface((50,110),pygame.SRCALPHA)
            pygame.draw.rect(gs,(0,180,255,a),gs.get_rect(),border_radius=3)
            surf.blit(gs,(px2-10,y-10),special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(surf,(18,28,72),(x,y,250,16),border_radius=4)
        pygame.draw.rect(surf,(0,180,255),(x,y,250,16),1,border_radius=4)
        fs=pygame.font.SysFont("consolas",13,bold=True)
        sign=fs.render("AD-ITYA SAM ROCKS ACADEMY",True,(0,220,255))
        surf.blit(sign,(x+125-sign.get_width()//2,y-24))
        ep=int(120+math.sin(t*3)*60)
        es=pygame.font.SysFont("consolas",14).render("[E] Enter Academy",True,(0,200,255))
        es.set_alpha(ep); surf.blit(es,(x+125-es.get_width()//2,y+96))

    def _draw_scooty(self,surf,x,y,t):
        pygame.draw.rect(surf,(14,24,64),(x,y,80,36),border_radius=10)
        pygame.draw.rect(surf,(0,200,255),(x,y,80,36),2,border_radius=10)
        gs=pygame.Surface((100,20),pygame.SRCALPHA)
        a=int(50+math.sin(t*3)*20)
        pygame.draw.ellipse(gs,(0,200,255,a),gs.get_rect())
        surf.blit(gs,(x-10,y+32),special_flags=pygame.BLEND_RGBA_ADD)
        ep=int(120+math.sin(t*3)*60)
        es=pygame.font.SysFont("consolas",14).render("[E] Flying Scooty",True,(0,200,255))
        es.set_alpha(ep); surf.blit(es,(x-es.get_width()//2+40,y-22))

    def draw_fg(self,surf): pass

# ══════════════════════════════════════════════════════════════════════
# ACADEMY MAP
# ══════════════════════════════════════════════════════════════════════
class AcademyMap(GameMap):
    def __init__(self):
        super().__init__('academy',960,640)
        self._floor=_floor_futuristic(TILE)
        self._colliders=[
            pygame.Rect(0,0,960,80), pygame.Rect(0,0,64,640),
            pygame.Rect(896,0,64,640), pygame.Rect(0,576,960,64),
            pygame.Rect(680,200,180,120),
            pygame.Rect(100,160,400,60), pygame.Rect(100,280,400,60),
        ]
        self._interact_zones=[(pygame.Rect(690,210,160,100),'lab_door')]
        self._trigger_zones= [(pygame.Rect(690,210,160,100),'lab_door')]

    def draw_bg(self,surf):
        cx,cy=self.camera.ix,self.camera.iy; t=self._t
        sx=-(cx%TILE); sy=-(cy%TILE)
        for fy in range(sy,H+TILE,TILE):
            for fx in range(sx,W+TILE,TILE):
                surf.blit(self._floor,(fx,fy))
        pygame.draw.rect(surf,(10,14,42),(0-cx,0-cy,960,80))
        pygame.draw.rect(surf,(0,80,160,60),(0-cx,78-cy,960,2))
        for i,(wx,wt) in enumerate([(120,"TIMELINE"),(350,"PHYSICS"),(600,"QUANTUM")]):
            self._draw_holo_display(surf,wx-cx,90-cy,wt,t+i*1.5)
        for i in range(6):
            dx=100+i*80
            for dy in [160,280]:
                pygame.draw.rect(surf,(18,26,70),(dx-cx,dy-cy,70,50),border_radius=4)
                pygame.draw.rect(surf,(0,100,200),(dx-cx,dy-cy,70,50),1,border_radius=4)
        self._draw_lab_door(surf,690-cx,200-cy,t)
        fs=pygame.font.SysFont("consolas",15,bold=True)
        sign=fs.render("▶ LAB WING — AUTHORIZED ACCESS",True,(0,200,255))
        surf.blit(sign,(W//2-sign.get_width()//2,10))

    def _draw_holo_display(self,surf,x,y,text,t):
        a=int(150+math.sin(t)*40)
        hs=pygame.Surface((160,60),pygame.SRCALPHA)
        pygame.draw.rect(hs,(0,80,200,30),hs.get_rect(),border_radius=4)
        pygame.draw.rect(hs,(0,180,255,a),hs.get_rect(),1,border_radius=4)
        fs=pygame.font.SysFont("consolas",13,bold=True)
        ts=fs.render(text,True,(0,220,255)); ts.set_alpha(a)
        hs.blit(ts,(80-ts.get_width()//2,22))
        surf.blit(hs,(x,y),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_lab_door(self,surf,x,y,t):
        pygame.draw.rect(surf,(12,20,62),(x,y,180,120),border_radius=6)
        pygame.draw.rect(surf,(0,180,255),(x,y,180,120),2,border_radius=6)
        a=int(80+math.sin(t*2)*30)
        gs=pygame.Surface((200,140),pygame.SRCALPHA)
        pygame.draw.rect(gs,(0,180,255,a),gs.get_rect(),border_radius=6)
        surf.blit(gs,(x-10,y-10),special_flags=pygame.BLEND_RGBA_ADD)
        fs=pygame.font.SysFont("consolas",13,bold=True)
        ts=fs.render("LAB-7",True,(0,220,255))
        surf.blit(ts,(x+90-ts.get_width()//2,y+48))
        ep=int(120+math.sin(t*3)*60)
        es=pygame.font.SysFont("consolas",12).render("[E] Enter Lab",True,(0,200,255))
        es.set_alpha(ep); surf.blit(es,(x+90-es.get_width()//2,y+126))

# ══════════════════════════════════════════════════════════════════════
# SCHOOL 2026
# ══════════════════════════════════════════════════════════════════════
class School2026Map(GameMap):
    def __init__(self):
        super().__init__('school_2026',960,640)
        self._floor=_floor_2026(TILE)
        self._colliders=[
            pygame.Rect(0,0,960,80), pygame.Rect(0,0,48,640),
            pygame.Rect(912,0,48,640), pygame.Rect(0,592,960,48),
            pygame.Rect(60,80,180,50), pygame.Rect(60,200,180,50),
            pygame.Rect(60,320,180,50), pygame.Rect(720,80,180,50),
            pygame.Rect(400,100,160,60),
        ]
        self._interact_zones=[
            (pygame.Rect(420,540,120,52),'exit_door'),
            (pygame.Rect(800,80,120,52),'rooftop_door'),
        ]
        self._trigger_zones=[
            (pygame.Rect(400,545,160,47),'exit_door'),
            (pygame.Rect(785,85,150,47),'rooftop_door'),
        ]

    def draw_bg(self,surf):
        cx,cy=self.camera.ix,self.camera.iy; t=self._t
        sx=-(cx%TILE); sy=-(cy%TILE)
        for fy in range(sy,H+TILE,TILE):
            for fx in range(sx,W+TILE,TILE):
                surf.blit(self._floor,(fx,fy))
        pygame.draw.rect(surf,(85,82,75),(0-cx,0-cy,960,80))
        fl_a=int(200+math.sin(t*12)*15+math.sin(t*7)*10)
        for lx in range(200,800,200):
            ls=pygame.Surface((120,16),pygame.SRCALPHA)
            pygame.draw.rect(ls,(220,220,200,fl_a),ls.get_rect(),border_radius=3)
            surf.blit(ls,(lx-cx-60,5-cy),special_flags=pygame.BLEND_RGBA_ADD)
        for i in range(4):
            for lx in [60,720]:
                lly=80+i*80
                self._draw_locker(surf,lx-cx,lly-cy)
        pygame.draw.rect(surf,(100,75,45),(400-cx,100-cy,160,60),border_radius=4)
        pygame.draw.rect(surf,(28,45,30),(200-cx,82-cy,400,60),border_radius=3)
        fs=pygame.font.SysFont("consolas",13)
        ts=fs.render("HISTORY - Chapter 12",True,(180,190,175))
        surf.blit(ts,(400-cx-ts.get_width()//2,104-cy))
        self._draw_door(surf,420-cx,542-cy,"▼ EXIT",t)
        self._draw_door(surf,800-cx,82-cy,"▲ ROOF",t)

    def _draw_locker(self,surf,x,y):
        for i in range(3):
            lx=x+i*18
            pygame.draw.rect(surf,(120,115,105),(lx,y,16,48),border_radius=2)
            pygame.draw.rect(surf,(90,85,78),(lx,y,16,48),1,border_radius=2)
            pygame.draw.circle(surf,(80,80,70),(lx+8,y+24),3)

    def _draw_door(self,surf,x,y,label,t):
        pygame.draw.rect(surf,(95,72,45),(x,y,90,52),border_radius=3)
        pygame.draw.rect(surf,(140,110,70),(x,y,90,52),1,border_radius=3)
        pygame.draw.circle(surf,(160,140,80),(x+78,y+26),5)
        fs=pygame.font.SysFont("consolas",12,bold=True)
        ts=fs.render(label,True,(220,200,160)); surf.blit(ts,(x+45-ts.get_width()//2,y+16))
        ep=int(140+math.sin(t*3)*80)
        es=pygame.font.SysFont("consolas",12).render("[E] Go",True,(255,230,100))
        es.set_alpha(ep); surf.blit(es,(x+45-es.get_width()//2,y+56))

# ══════════════════════════════════════════════════════════════════════
# STREETS 2026
# ══════════════════════════════════════════════════════════════════════
class Streets2026Map(GameMap):
    def __init__(self):
        super().__init__('streets_2026',1280,640)
        self._road=_road(TILE); self._pavement=_floor_2026(TILE)
        self._colliders=[
            pygame.Rect(0,0,1280,80), pygame.Rect(0,0,48,640),
            pygame.Rect(1232,0,48,640), pygame.Rect(0,592,1280,48),
            pygame.Rect(60,80,220,280), pygame.Rect(320,80,180,260),
            pygame.Rect(540,80,200,280), pygame.Rect(780,80,180,260),
            pygame.Rect(1000,80,200,280),
        ]
        self._interact_zones=[(pygame.Rect(1010,460,200,110),'tea_shop')]
        self._trigger_zones= [(pygame.Rect(1010,460,200,110),'tea_shop')]
        self._puddles=[{'x':random.randint(100,1200),'y':random.randint(400,560),
                        'r':random.randint(12,30)} for _ in range(18)]

    def update(self,dt): super().update(dt)

    def draw_bg(self,surf):
        cx,cy=self.camera.ix,self.camera.iy; t=self._t
        for i in range(H):
            c=int(4+i/H*12); pygame.draw.line(surf,(c,c,c+8),(0,i),(W,i))
        sx=-(cx%TILE)
        for fy in range(360-cy,H+TILE,TILE):
            for fx in range(sx,W+TILE,TILE):
                surf.blit(self._pavement,(fx,fy))
        for fx in range(sx,W+TILE,TILE):
            for fi in range(3):
                surf.blit(self._road,(fx,400-cy+fi*TILE))
        for lx in range(-(cx%120),W,120):
            pygame.draw.rect(surf,(55,55,65),(lx,420-cy,60,3))
        for bx,bw,bh in [(60,220,280),(320,180,260),(540,200,280),(780,180,260),(1000,200,280)]:
            self._draw_building_2026(surf,bx-cx,80-cy,bw,bh,t)
        for lx in range(160,1200,240):
            self._draw_streetlight(surf,lx-cx,340-cy,t)
        for p in self._puddles:
            self._draw_puddle(surf,p['x']-cx,p['y']-cy,p['r'],t)
        for px2 in range(120,1100,280):
            self._draw_car_2026(surf,px2-cx,450-cy)
        self._draw_tea_shop(surf,1010-cx,360-cy,t)

    def _draw_building_2026(self,surf,x,y,w,h,t):
        if x+w<0 or x>W: return
        pygame.draw.rect(surf,(55,52,50),(x,y,w,h),border_radius=2)
        pygame.draw.rect(surf,(68,65,62),(x+3,y+3,w-6,h-6))
        for wy in range(y+10,y+h-10,18):
            for wx in range(x+8,x+w-8,14):
                lit=(wx*3+wy*7+int(t*0.3))%5!=0
                pygame.draw.rect(surf,(200,180,140) if lit else (30,28,25),(wx,wy,8,12))

    def _draw_streetlight(self,surf,x,y,t):
        pygame.draw.rect(surf,(55,55,60),(x,y,6,120),border_radius=2)
        pygame.draw.rect(surf,(60,60,65),(x-20,y-8,46,12),border_radius=4)
        a=int(60+math.sin(t*0.5)*10)
        gs=pygame.Surface((100,80),pygame.SRCALPHA)
        pygame.draw.ellipse(gs,(255,220,140,a),(10,10,80,60))
        surf.blit(gs,(x-47,y+4),special_flags=pygame.BLEND_RGBA_ADD)

    def _draw_puddle(self,surf,x,y,r,t):
        ps=pygame.Surface((r*2+4,r*2+4),pygame.SRCALPHA)
        a=int(40+math.sin(t*2+x*0.05)*15)
        pygame.draw.ellipse(ps,(80,100,140,a),(2,r//2,r*2,r))
        surf.blit(ps,(x-r-2,y-r//2-2))

    def _draw_car_2026(self,surf,x,y):
        if x+90<0 or x>W: return
        pygame.draw.rect(surf,(45,45,55),(x,y,90,32),border_radius=6)
        pygame.draw.rect(surf,(35,35,45),(x+12,y-12,66,20),border_radius=4)
        pygame.draw.circle(surf,(60,60,70),(x+14,y+32),9)
        pygame.draw.circle(surf,(60,60,70),(x+76,y+32),9)

    def _draw_tea_shop(self,surf,x,y,t):
        pygame.draw.rect(surf,(55,40,30),(x,y,200,200),border_radius=4)
        pygame.draw.rect(surf,(70,52,38),(x+5,y+5,190,190))
        a=int(180+math.sin(t*1.5)*30)
        ws=pygame.Surface((80,60),pygame.SRCALPHA); ws.fill((255,200,140,a))
        surf.blit(ws,(x+20,y+40),special_flags=pygame.BLEND_RGBA_ADD)
        pygame.draw.rect(surf,(90,70,50),(x+18,y+38,84,64),2)
        pygame.draw.rect(surf,(40,28,18),(x+20,y+14,160,24),border_radius=3)
        fs=pygame.font.SysFont("consolas",13)
        ts=fs.render("☕  TEA & STAY",True,(255,210,150))
        surf.blit(ts,(x+100-ts.get_width()//2,y+18))
        pygame.draw.rect(surf,(50,35,22),(x+76,y+150,48,50),border_radius=3)
        pygame.draw.circle(surf,(160,140,80),(x+116,y+176),4)
        ep=int(120+math.sin(t*3)*60)
        es=pygame.font.SysFont("consolas",14).render("[E] Enter Tea Shop",True,(255,200,120))
        es.set_alpha(ep); surf.blit(es,(x+100-es.get_width()//2,y+206))

# ══════════════════════════════════════════════════════════════════════
# TEA SHOP INTERIOR
# ══════════════════════════════════════════════════════════════════════
class TeaShopMap(GameMap):
    def __init__(self):
        super().__init__('tea_shop',800,540)
        self._floor=_floor_wood(TILE)
        self._colliders=[
            pygame.Rect(0,0,800,80), pygame.Rect(0,0,48,540),
            pygame.Rect(752,0,48,540), pygame.Rect(0,492,800,48),
            pygame.Rect(280,120,240,80),
            pygame.Rect(80,280,100,80), pygame.Rect(240,280,100,80),
            pygame.Rect(560,280,100,80),
        ]
        self._interact_zones=[(pygame.Rect(290,130,220,68),'counter')]
        self._trigger_zones= []

    def draw_bg(self,surf):
        cx,cy=self.camera.ix,self.camera.iy; t=self._t
        sx=-(cx%TILE); sy=-(cy%TILE)
        for fy in range(sy,H+TILE,TILE):
            for fx in range(sx,W+TILE,TILE):
                surf.blit(self._floor,(fx,fy))
        pygame.draw.rect(surf,(60,45,30),(0-cx,0-cy,800,80))
        self._draw_window_rain(surf,100-cx,90-cy,200,120,t)
        self._draw_window_rain(surf,500-cx,90-cy,200,120,t)
        pygame.draw.rect(surf,(80,58,35),(280-cx,120-cy,240,80),border_radius=4)
        pygame.draw.rect(surf,(110,82,50),(288-cx,124-cy,224,68),border_radius=3)
        pygame.draw.ellipse(surf,(80,60,40),(354-cx,140-cy,42,34))
        for i in range(3):
            a=int(100+math.sin(t*2+i)*40)
            ss=pygame.Surface((6,20),pygame.SRCALPHA)
            pygame.draw.line(ss,(255,255,255,a),(3,20),(3+int(math.sin(t+i)*3),0),1)
            surf.blit(ss,(358-cx+i*8,120-cy-15))
        for tx2 in [80,240,560]:
            self._draw_table(surf,tx2-cx,280-cy)
        self._draw_tv(surf,600-cx,90-cy,t)
        warm=pygame.Surface((W,H),pygame.SRCALPHA)
        pygame.draw.ellipse(warm,(255,160,80,18),(0,0,W,H//2))
        surf.blit(warm,(0,0))
        ep=int(120+math.sin(t*3)*60)
        es=pygame.font.SysFont("consolas",14).render("[E] Talk to Owner",True,(255,200,120))
        es.set_alpha(ep); surf.blit(es,(280-cx+120-es.get_width()//2,200-cy))

    def _draw_window_rain(self,surf,x,y,w,h,t):
        ws=pygame.Surface((w,h),pygame.SRCALPHA)
        for i in range(h):
            c=int(12+i/h*20); pygame.draw.line(ws,(c,c,c+30,220),(0,i),(w,i))
        for i in range(20):
            rx=int((i*37+t*80)%w); ry=int((i*23+t*200)%h); rl=random.randint(8,18)
            pygame.draw.line(ws,(100,120,180,80),(rx,ry),(rx+2,min(ry+rl,h)),1)
        pygame.draw.rect(ws,(80,65,45,255),(0,0,w,h),3)
        surf.blit(ws,(x,y))

    def _draw_table(self,surf,x,y):
        pygame.draw.rect(surf,(100,72,44),(x,y,100,10),border_radius=3)
        pygame.draw.rect(surf,(80,58,34),(x+10,y+10,8,50),border_radius=2)
        pygame.draw.rect(surf,(80,58,34),(x+82,y+10,8,50),border_radius=2)
        pygame.draw.ellipse(surf,(100,80,55),(x+20,y-8,22,14))
        pygame.draw.ellipse(surf,(100,80,55),(x+60,y-8,22,14))

    def _draw_tv(self,surf,x,y,t):
        pygame.draw.rect(surf,(30,30,35),(x,y,140,80),border_radius=4)
        pygame.draw.rect(surf,(20,20,25),(x,y,140,80),1,border_radius=4)
        fl=int(180+math.sin(t*8)*20)
        screen_s=pygame.Surface((128,68),pygame.SRCALPHA)
        screen_s.fill((fl//8,fl//6,fl//4,240))
        fs=pygame.font.SysFont("consolas",10)
        news=fs.render("BREAKING: Iran-US Conflict",True,(220,60,60))
        news.set_alpha(fl); screen_s.blit(news,(4,50))
        surf.blit(screen_s,(x+6,y+6))

# ══════════════════════════════════════════════════════════════════════
# Factory
# ══════════════════════════════════════════════════════════════════════
_REG = {}
def get_map(name:str)->GameMap:
    if name not in _REG:
        _MAP = {'apartment':ApartmentMap,'valora':ValoraStreetMap,
                'academy':AcademyMap,'school_2026':School2026Map,
                'streets_2026':Streets2026Map,'tea_shop':TeaShopMap}
        cls=_MAP.get(name)
        if cls is None: raise KeyError(f"Unknown map: {name!r}")
        _REG[name]=cls()
    return _REG[name]