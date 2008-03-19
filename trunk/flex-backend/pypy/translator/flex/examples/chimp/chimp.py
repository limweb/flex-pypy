#/usr/bin/env python
"""
This simple example has very little to do with the pygame
chimp example, except that it will act the same (more or less)
and it uses the same resources, only they got converted to
mp3s, pngs.
"""


#Import Modules
from pypy.translator.flex.modules.flex import *
from pypy.rpython.ootypesystem.bltregistry import BasicExternal, MethodDesc

class MyRect:
    def __init__(self,x,y,w,h):
        self.x, self.y,self.w,self.h = x,y,w,h

SCREEN_W = 468
SCREEN_H = 80

class Game:
    def __init__(self):pass
    
    def init(self,screen):
        self.screen = screen
        screen.layout = 'absolute'
        screen.setActualSize(SCREEN_W, SCREEN_H)
        
        screen.addEventListener('mouseMove',mousemotion)
        screen.addEventListener('enterFrame',do_loop)
        screen.addEventListener('click',chimp_whip)
        
        img  = self._chimp = Image() 
        img.load("data/chimp.png")
        img.move(0,0)

        c = self.chimp = Sprite()
        self.chimp.addChild(img)
        cw = castToSpriteWindow(screen)
        #cw.addChild(c)

        #self.screen.addChild(img)
        
        img2 = self.fist =  Image()
        img2.load("data/fist.png")
        self.screen.addChild(img2)
        img2.move(400,0)
        self.move = 1
        self.spin = 0
        
        self.sfx = {}
        s = self.sfx['whip'] = Sound()
        s.load(newURLRequest("data/punch.mp3"))
    def loop(self):
        img = self.chimp
        img.x += self.move * 4
        if img.x > SCREEN_W-img.width:
            self.move = -1
        if img.x < 0:
            self.move = 1
        if self.spin:
            self.spin -= 1
            img.rotation = self.spin*49
        pass
    
    def paint(self,screen):
        pass
game = Game()

def mousemotion(e):
    img = game.fist
    img_halfw = img.width / 2
    newx = e.stageX - img_halfw
    
    # don't reach the borders
    if e.stageX > SCREEN_W - img_halfw:
        newx = SCREEN_W - img.width
    if newx <= 0:
        newx = 0

    img.x = newx

def do_loop(e):
    game.loop()

def chimp_whip(e):
    img = game.chimp
    if e.stageX > img.x and e.stageX < img.x+img.width:
        game.sfx['whip'].play()
        game.spin = 20
    


def flash_main( x=1 ):
    game.init(castToWindow(x))
    
    
