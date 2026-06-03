import pygame, math

class MissionBox:
    def __init__(self,f_sm,f_xs):
        self.f_sm=f_sm; self.f_xs=f_xs
        self.title=""; self.text=""; self.alpha=0.0; self.target=0.0
    def show(self,text,title="OBJECTIVE"): self.text=text; self.title=title; self.target=218.0
    def hide(self): self.target=0.0
    def update(self,dt): self.alpha+=(self.target-self.alpha)*min(1,dt*6)
    def draw(self,surf,W):
        al=int(self.alpha)
        if al<4: return
        tw=max(self.f_sm.size(self.text)[0]+24,200); h=58; x=W-tw-14; y=14
        s=pygame.Surface((tw,h),pygame.SRCALPHA)
        pygame.draw.rect(s,(6,12,42,min(al,210)),(0,0,tw,h),border_radius=8)
        pygame.draw.rect(s,(0,155,255,min(al,160)),(0,0,tw,h),1,border_radius=8)
        pygame.draw.rect(s,(0,155,255,min(al,140)),(0,0,4,h),border_radius=4)
        t1=self.f_xs.render(f"● {self.title}",True,(0,190,255)); s.blit(t1,(10,8))
        t2=self.f_sm.render(self.text,True,(200,218,255))
        if t2.get_width()>tw-20: t2=self.f_xs.render(self.text[:38]+'…',True,(200,218,255))
        s.blit(t2,(10,30)); surf.blit(s,(x,y))

class HUD:
    def __init__(self,f_sm,f_xs):
        self.f_sm=f_sm; self.f_xs=f_xs
        self.location="Valora City"; self.year="2187"
        self.ctrl_alpha=255.0; self.ctrl_t=7.0
    def update(self,dt):
        if self.ctrl_t>0:
            self.ctrl_t-=dt
            if self.ctrl_t<=0: self.ctrl_alpha=0.0
        elif self.ctrl_alpha>0: self.ctrl_alpha=max(0,self.ctrl_alpha-dt*80)
    def draw(self,surf,W,H):
        txt=f"  {self.location}  ·  {self.year}  "
        ts=self.f_xs.render(txt,True,(170,205,255))
        bg=pygame.Surface((ts.get_width()+12,ts.get_height()+8),pygame.SRCALPHA)
        pygame.draw.rect(bg,(6,12,42,180),(0,0)+bg.get_size(),border_radius=6)
        pygame.draw.rect(bg,(0,110,190,140),(0,0)+bg.get_size(),1,border_radius=6)
        bg.blit(ts,(6,4)); surf.blit(bg,(12,12))
        al=int(self.ctrl_alpha)
        if al>5:
            for i,(txt2,col) in enumerate([("WASD/Arrows: Move",(160,190,240)),
                                           ("E / Z: Interact",(160,190,240)),
                                           ("SHIFT: Sprint",(140,170,220)),
                                           ("ESC: Menu",(130,160,210))]):
                cs=self.f_xs.render(txt2,True,col); cs.set_alpha(al)
                surf.blit(cs,(14,H-85+i*18))

class FadeScreen:
    def __init__(self):
        self.alpha=0.0; self.dir=0; self.speed=280.0
        self.on_done=None; self.color=(0,0,0)
    def fade_out(self,speed=280,on_done=None,color=(0,0,0)):
        self.alpha=0.0;self.dir=1;self.speed=speed;self.on_done=on_done;self.color=color
    def fade_in(self,speed=280,color=(0,0,0)):
        self.alpha=255.0;self.dir=-1;self.speed=speed;self.color=color
    def set_black(self): self.alpha=255.0; self.dir=0
    def set_clear(self): self.alpha=0.0; self.dir=0
    def update(self,dt):
        if self.dir==0: return
        self.alpha+=self.dir*self.speed*dt
        if self.dir==1 and self.alpha>=255:
            self.alpha=255.0; self.dir=0
            if self.on_done: self.on_done()
        elif self.dir==-1 and self.alpha<=0:
            self.alpha=0.0; self.dir=0
    def draw(self,surf,W,H):
        if self.alpha<1: return
        s=pygame.Surface((W,H)); s.fill(self.color); s.set_alpha(int(self.alpha)); surf.blit(s,(0,0))
    @property
    def busy(self): return self.dir!=0
    @property
    def opaque(self): return self.alpha>=255

class PauseMenu:
    def __init__(self,f_lg,f_md,f_sm):
        self.f_lg=f_lg;self.f_md=f_md;self.f_sm=f_sm
        self.active=False; self.sel=0; self.al=0.0
        self.items=['Resume','Save Game','Load Game','Quit']
    def open(self): self.active=True; self.sel=0; self.al=0.0
    def close(self): self.active=False
    def update(self,dt):
        if self.active: self.al=min(220.0,self.al+dt*500)
    def key(self,k,audio=None):
        if k==pygame.K_UP: self.sel=(self.sel-1)%len(self.items); audio and audio.play_sfx('blip')
        elif k==pygame.K_DOWN: self.sel=(self.sel+1)%len(self.items); audio and audio.play_sfx('blip')
        elif k in(pygame.K_RETURN,pygame.K_z,pygame.K_e):
            audio and audio.play_sfx('confirm')
            return self.items[self.sel]
        return None
    def draw(self,surf,W,H):
        if not self.active: return
        al=int(self.al)
        ov=pygame.Surface((W,H),pygame.SRCALPHA); ov.fill((0,4,20,min(al,185))); surf.blit(ov,(0,0))
        pw,ph=280,310; px,py=W//2-pw//2,H//2-ph//2
        p=pygame.Surface((pw,ph),pygame.SRCALPHA)
        pygame.draw.rect(p,(6,12,48,min(al,218)),(0,0,pw,ph),border_radius=12)
        pygame.draw.rect(p,(0,155,255,min(al,200)),(0,0,pw,ph),2,border_radius=12)
        tl=self.f_lg.render("PAUSED",True,(0,215,255)); p.blit(tl,(pw//2-tl.get_width()//2,18))
        pygame.draw.line(p,(0,90,160),(18,58),(pw-18,58),1)
        for i,item in enumerate(self.items):
            sel=i==self.sel; col=(0,220,255) if sel else (150,180,215)
            if sel:
                pygame.draw.rect(p,(0,55,115,115),(8,68+i*48,pw-16,40),border_radius=7)
                pygame.draw.rect(p,(0,130,210,180),(8,68+i*48,pw-16,40),1,border_radius=7)
            it=self.f_md.render(item,True,col); p.blit(it,(pw//2-it.get_width()//2,78+i*48))
        surf.blit(p,(px,py))

class CharIntroCard:
    def __init__(self,f_lg,f_sm):
        self.f_lg=f_lg;self.f_sm=f_sm
        self.active=False;self.name="";self.title="";self.art=None
        self.timer=0.0;self.dur=3.5;self.al=0.0;self.phase='in';self.on_done=None
    def show(self,name,title,art,dur=3.5,on_done=None):
        self.name=name;self.title=title;self.art=art;self.dur=dur
        self.active=True;self.timer=0.0;self.al=0.0;self.phase='in';self.on_done=on_done
    def update(self,dt):
        if not self.active: return
        self.timer+=dt
        if self.phase=='in':
            self.al=min(255.0,self.al+dt*350)
            if self.al>=255: self.phase='hold'
        elif self.phase=='hold':
            if self.timer>self.dur-0.9: self.phase='out'
        elif self.phase=='out':
            self.al=max(0.0,self.al-dt*350)
            if self.al<=0:
                self.active=False
                if self.on_done: self.on_done()
    def draw(self,surf,W,H):
        if not self.active: return
        al=int(self.al); pw,ph=440,112; px=72; py=H//2-ph//2
        s=pygame.Surface((pw,ph),pygame.SRCALPHA)
        pygame.draw.rect(s,(5,10,38,min(al,210)),(0,0,pw,ph),border_radius=8)
        pygame.draw.rect(s,(0,175,255,min(al,180)),(0,0,pw,ph),2,border_radius=8)
        pygame.draw.rect(s,(0,140,200,min(al,220)),(0,0,5,ph))
        n=self.f_lg.render(self.name,True,(0,215,255)); na=n.copy(); na.set_alpha(al); s.blit(na,(18,18))
        t=self.f_sm.render(self.title,True,(155,195,235)); ta=t.copy(); ta.set_alpha(al); s.blit(ta,(18,62))
        pygame.draw.line(s,(0,140,200,min(al,150)),(18,58),(pw-18,58),1)
        surf.blit(s,(px,py))
        if self.art:
            from sprites import draw_char,CW,CH
            bs=4; cs=pygame.Surface(((CW+2)*bs,(CH+2)*bs),pygame.SRCALPHA)
            draw_char(cs,self.art,0,0,bs); cs.set_alpha(al)
            surf.blit(cs,(px-CW*bs-10,py-12))