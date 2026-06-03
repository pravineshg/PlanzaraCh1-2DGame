import pygame, math

class DialogueLine:
    def __init__(self,speaker,text): self.speaker=speaker; self.text=text

class DialogueEngine:
    SPEED=38
    def __init__(self,fonts):
        self.f_name,self.f_text,self.f_xs=fonts
        self.active=False; self.lines=[]; self.idx=0
        self.pos=0.0; self.on_done=None; self.alpha=0.0
    def start(self,lines,on_done=None):
        self.lines=[]
        for l in lines:
            if isinstance(l,tuple): self.lines.append(DialogueLine(l[0],l[1]))
            else: self.lines.append(l)
        self.idx=0; self.pos=0.0; self.active=True; self.alpha=0.0; self.on_done=on_done
    def advance(self,audio=None):
        if not self.active: return False
        line=self.lines[self.idx]
        if int(self.pos)<len(line.text):
            self.pos=float(len(line.text))
            if audio: audio.play_sfx('confirm')
        else:
            self.idx+=1
            if self.idx>=len(self.lines):
                self.active=False
                if self.on_done: self.on_done()
                return False
            self.pos=0.0
            if audio: audio.play_sfx('blip')
        return True
    def update(self,dt):
        if not self.active: return
        self.alpha=min(220.0,self.alpha+dt*600)
        if self.idx<len(self.lines):
            line=self.lines[self.idx]
            if self.pos<len(line.text): self.pos=min(self.pos+self.SPEED*dt,float(len(line.text)))
    def draw(self,surf,W,H):
        al=int(self.alpha)
        if al<4: return
        bx,by,bw,bh=30,H-148,W-60,128
        box=pygame.Surface((bw,bh),pygame.SRCALPHA)
        pygame.draw.rect(box,(6,12,42,min(al,215)),(0,0,bw,bh),border_radius=10)
        pygame.draw.rect(box,(0,155,255,min(al,170)),(0,0,bw,bh),2,border_radius=10)
        for cx2,cy2 in[(0,0),(bw-18,0),(0,bh-18),(bw-18,bh-18)]:
            pygame.draw.rect(box,(0,200,255,min(al,160)),(cx2,cy2,18,18),border_radius=4)
            pygame.draw.rect(box,(0,150,220,min(al,200)),(cx2,cy2,18,18),1,border_radius=4)
        surf.blit(box,(bx,by))
        if not self.active or self.idx>=len(self.lines): return
        line=self.lines[self.idx]; shown=line.text[:int(self.pos)]
        if line.speaker:
            ns=self.f_name.render(line.speaker,True,(0,220,255))
            nb=pygame.Surface((ns.get_width()+18,ns.get_height()+8),pygame.SRCALPHA)
            pygame.draw.rect(nb,(5,18,58,min(al,210)),(0,0)+nb.get_size(),border_radius=5)
            pygame.draw.rect(nb,(0,140,220,min(al,180)),(0,0)+nb.get_size(),1,border_radius=5)
            nb.blit(ns,(9,4)); surf.blit(nb,(bx+14,by-nb.get_height()-2))
        words=shown.split(' '); rows=[]; row=''
        for w in words:
            test=(row+' '+w).strip()
            if self.f_text.size(test)[0]<bw-44: row=test
            else:
                if row: rows.append(row)
                row=w
        if row: rows.append(row)
        for i,r in enumerate(rows[:3]):
            ts=self.f_text.render(r,True,(215,232,255)); surf.blit(ts,(bx+18,by+16+i*30))
        if int(self.pos)>=len(line.text) and (pygame.time.get_ticks()//480)%2==0:
            ax,ay=bx+bw-24,by+bh-18
            pygame.draw.polygon(surf,(0,220,255),[(ax-8,ay),(ax+8,ay),(ax,ay+10)])
        ts2=self.f_xs.render(f"{self.idx+1}/{len(self.lines)}",True,(80,110,160))
        surf.blit(ts2,(bx+bw-ts2.get_width()-10,by+8))