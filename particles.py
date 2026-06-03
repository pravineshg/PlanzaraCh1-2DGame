import pygame, math, random

class Particle:
    __slots__ = ['x','y','vx','vy','color','life','max_life','size','gravity']
    def __init__(self,x,y,vx,vy,color,life,size=3,gravity=0):
        self.x=x;self.y=y;self.vx=vx;self.vy=vy;self.color=color
        self.life=life;self.max_life=life;self.size=size;self.gravity=gravity
    def update(self,dt):
        self.x+=self.vx*dt;self.y+=self.vy*dt;self.vy+=self.gravity*dt;self.life-=dt
        return self.life>0

class ParticleSystem:
    def __init__(self): self.particles=[]

    def emit(self,x,y,color,count=1,speed=80,spread=360,size=3,life=1.0,gravity=0):
        for _ in range(count):
            a=math.radians(random.uniform(0,spread))
            spd=random.uniform(speed*0.5,speed)
            l=random.uniform(life*0.6,life); s=random.randint(max(1,size-1),size+1)
            self.particles.append(Particle(x,y,math.cos(a)*spd,math.sin(a)*spd,color,l,s,gravity))

    def emit_dir(self,x,y,color,angle_deg,spread=20,count=3,speed=120,life=0.8,size=2):
        for _ in range(count):
            a=math.radians(angle_deg+random.uniform(-spread,spread))
            spd=random.uniform(speed*0.7,speed); l=random.uniform(life*0.6,life)
            self.particles.append(Particle(x,y,math.cos(a)*spd,math.sin(a)*spd,color,l,size))

    def update(self,dt): self.particles=[p for p in self.particles if p.update(dt)]

    def draw(self,surf,cx=0,cy=0):
        for p in self.particles:
            ratio=p.life/p.max_life; al=max(0,min(255,int(255*ratio)))
            r,g,b=p.color[0],p.color[1],p.color[2]
            s=p.size
            if s<2:
                x,y=int(p.x-cx),int(p.y-cy)
                if 0<=x<surf.get_width() and 0<=y<surf.get_height():
                    surf.set_at((x,y),(r,g,b,al))
            else:
                ss=pygame.Surface((s*2,s*2),pygame.SRCALPHA)
                pygame.draw.circle(ss,(r,g,b,al),(s,s),s)
                surf.blit(ss,(int(p.x-cx-s),int(p.y-cy-s)))

    def clear(self): self.particles=[]

    def count(self): return len(self.particles)


class RainSystem:
    def __init__(self,w,h,density=200):
        self.w=w;self.h=h
        self.drops=[{'x':random.randint(0,w),'y':random.randint(0,h),
                     'speed':random.uniform(400,700),'len':random.randint(8,20),
                     'al':random.randint(35,90)} for _ in range(density)]
    def update(self,dt):
        for d in self.drops:
            d['y']+=d['speed']*dt; d['x']+=d['speed']*0.08*dt
            if d['y']>self.h: d['y']=random.randint(-20,0); d['x']=random.randint(0,self.w)
    def draw(self,surf):
        rs=pygame.Surface((self.w,self.h),pygame.SRCALPHA)
        for d in self.drops:
            x1,y1=int(d['x']),int(d['y']); x2=x1+int(d['len']*0.08); y2=y1+d['len']
            pygame.draw.line(rs,(180,200,255,d['al']),(x1,y1),(x2,y2),1)
        surf.blit(rs,(0,0))


def glow_circle(surf,x,y,radius,color,alpha=60):
    s=pygame.Surface((radius*2,radius*2),pygame.SRCALPHA)
    for r in range(radius,0,-4):
        a=int(alpha*(1-r/radius)**0.7)
        if a>0: pygame.draw.circle(s,(*color[:3],a),(radius,radius),r)
    surf.blit(s,(x-radius,y-radius),special_flags=pygame.BLEND_RGBA_ADD)

def neon_rect(surf,rect,color,alpha=40,width=2,glow=8):
    pygame.draw.rect(surf,color,rect,width)
    gs=pygame.Surface((rect.width+glow*2,rect.height+glow*2),pygame.SRCALPHA)
    pygame.draw.rect(gs,(*color[:3],alpha),(glow,glow,rect.width,rect.height),width+2)
    surf.blit(gs,(rect.x-glow,rect.y-glow),special_flags=pygame.BLEND_RGBA_ADD)