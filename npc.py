import pygame, math, random
from sprites import draw_char, CW, CH

class NPC:
    def __init__(self,x,y,art,name="NPC",direction='down',dialogue=None,
                 wander=False,fixed_face=None):
        self.pos=pygame.Vector2(x,y)
        self.art=art; self.name=name; self.dir=direction
        self.fixed_face=fixed_face
        self.frame=0; self.anim_t=0.0; self.t=random.random()*6
        self.rect=pygame.Rect(int(x)-14,int(y)-8,28,16)
        self.dialogue=dialogue or []; self.didx=0
        self.wander=wander; self.wander_t=0.0; self.wander_dir=direction
        self.visible=True; self.highlight=False
        self.interact_r=72; self.bs=4

    def update(self,dt):
        self.t+=dt
        if self.wander:
            self.wander_t+=dt
            if self.wander_t>random.uniform(1.8,4.2):
                self.wander_t=0
                self.wander_dir=random.choice(['up','down','left','right','none','none'])
            self.dir=self.wander_dir if self.wander_dir!='none' else self.dir
        if self.fixed_face: self.dir=self.fixed_face
        self.anim_t+=dt
        if self.anim_t>0.18: self.anim_t=0; self.frame=1-self.frame

    def in_range(self,px,py):
        dx=px-self.rect.centerx; dy=py-self.rect.centery
        return dx*dx+dy*dy<self.interact_r**2

    def next_dialogue(self)->str|None:
        if not self.dialogue: return None
        line=self.dialogue[self.didx%len(self.dialogue)]
        self.didx+=1; return line

    def set_pos(self,x,y):
        self.pos=pygame.Vector2(x,y)
        self.rect.centerx=int(x); self.rect.centery=int(y)

    def draw(self,surf,cam_x,cam_y):
        if not self.visible: return
        bs=self.bs; cx=self.rect.centerx; cy=self.rect.centery
        ox=cx-cam_x-(CW*bs//2); oy=cy-cam_y-(CH*bs)+8
        sh=pygame.Surface((CW*bs,14),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,50),(4,2,CW*bs-8,10))
        surf.blit(sh,(ox,cy-cam_y-6))
        flip=(self.dir=='left')
        if flip:
            tmp=pygame.Surface(((CW+2)*bs,(CH+2)*bs),pygame.SRCALPHA)
            draw_char(tmp,self.art,0,0,bs); tmp=pygame.transform.flip(tmp,True,False)
            surf.blit(tmp,(ox,oy))
        else:
            draw_char(surf,self.art,ox,oy,bs)
        if self.highlight:
            bob=math.sin(self.t*3)*3
            ind=pygame.Surface((20,20),pygame.SRCALPHA)
            pygame.draw.circle(ind,(0,220,255,180),(10,10),9)
            pygame.draw.circle(ind,(255,255,255,200),(10,10),9,2)
            surf.blit(ind,(cx-cam_x-10,oy-16+int(bob)))