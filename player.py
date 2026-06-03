import pygame, math
from sprites import draw_char, MITS, SUZEN, REZA, CW, CH

SPEED = 155
SPRINT = 270

class Player:
    ARTS = {'mits':None,'suzen':None,'reza':None}

    def __init__(self,x,y,character='mits'):
        self.pos=pygame.Vector2(x,y)
        self.dir='down'; self.frame=0; self.anim_t=0.0
        self.character=character; self.moving=False
        self.rect=pygame.Rect(int(x)-14,int(y)-8,28,16)
        self.sprinting=False; self.can_move=True
        self.interact_cd=0.0; self.step_t=0.0
        self._art_cache={}

    @property
    def art(self):
        arts={'mits':MITS,'suzen':SUZEN,'reza':REZA}
        return arts.get(self.character,MITS)

    @property
    def cx(self): return self.rect.centerx
    @property
    def cy(self): return self.rect.centery
    @property
    def world_pos(self): return pygame.Vector2(self.cx,self.cy)

    def set_pos(self,x,y):
        self.pos=pygame.Vector2(x,y)
        self.rect.centerx=int(x); self.rect.centery=int(y)

    def face_pos(self,tx,ty):
        dx=tx-self.cx; dy=ty-self.cy
        if abs(dx)>abs(dy): self.dir='right' if dx>0 else 'left'
        else: self.dir='down' if dy>0 else 'up'

    def update(self,dt,colliders):
        self.interact_cd=max(0,self.interact_cd-dt)
        if not self.can_move: self.moving=False; self.frame=0; return
        keys=pygame.key.get_pressed()
        mv=pygame.Vector2(0,0)
        if keys[pygame.K_w] or keys[pygame.K_UP]:    mv.y-=1; self.dir='up'
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:  mv.y+=1; self.dir='down'
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:  mv.x-=1; self.dir='left'
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: mv.x+=1; self.dir='right'
        self.sprinting=keys[pygame.K_LSHIFT]
        self.moving=mv.length_squared()>0
        if self.moving:
            spd=(SPRINT if self.sprinting else SPEED)*dt
            mv=mv.normalize()*spd
            self._slide(mv.x,0,colliders); self._slide(0,mv.y,colliders)
            self.anim_t+=dt
            if self.anim_t>=0.14: self.anim_t=0; self.frame=1-self.frame
        else: self.frame=0

    def _slide(self,dx,dy,colliders):
        self.rect.x+=int(dx); self.pos.x=self.rect.centerx
        for c in colliders:
            if self.rect.colliderect(c):
                if dx>0: self.rect.right=c.left
                elif dx<0: self.rect.left=c.right
                self.pos.x=self.rect.centerx
        self.rect.y+=int(dy); self.pos.y=self.rect.centery
        for c in colliders:
            if self.rect.colliderect(c):
                if dy>0: self.rect.bottom=c.top
                elif dy<0: self.rect.top=c.bottom
                self.pos.y=self.rect.centery

    def interact_point(self):
        d=44; cx,cy=self.cx,self.cy
        if self.dir=='up':    return (cx,cy-d)
        if self.dir=='down':  return (cx,cy+d)
        if self.dir=='left':  return (cx-d,cy)
        return (cx+d,cy)

    def draw(self,surf,cam_x,cam_y,bs=4,flip=False):
        ox=self.cx-cam_x-(CW*bs//2)
        oy=self.cy-cam_y-(CH*bs)+8
        # shadow
        sh=pygame.Surface((CW*bs,14),pygame.SRCALPHA)
        pygame.draw.ellipse(sh,(0,0,0,55),(4,2,CW*bs-8,10))
        surf.blit(sh,(ox,self.cy-cam_y-6))
        # flip for left direction
        if flip or self.dir=='left':
            tmp=pygame.Surface(((CW+2)*bs,(CH+2)*bs),pygame.SRCALPHA)
            draw_char(tmp,self.art,0,0,bs)
            tmp=pygame.transform.flip(tmp,True,False)
            surf.blit(tmp,(ox,oy))
        else:
            draw_char(surf,self.art,ox,oy,bs)