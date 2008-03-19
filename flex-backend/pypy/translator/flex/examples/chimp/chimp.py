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

        self.chimp = load_sprite("py_chimp_png");
        self.screen.addChild(self.chimp)

        self.orig_y = self.chimp.y
        
        img2 = self.fist = load_sprite("py_fist_png")
        self.screen.addChild(img2)
        img2.move(400,img2.height/2)
        self.move = 1
        self.spin = 0
        self.hit = 0
        self.hit_move = 1
        
        self.sfx = {}
        self.sfx['whip'] = load_sound_resource("py_punch_mp3")
        self.sfx['nohit'] = load_sound_resource("py_whiff_mp3")

    def loop(self):
        img = self.chimp
        if self.spin:
            self.spin -= 1
            img.rotation = self.spin*24
        else:
            img.x += self.move * 8
            if img.x > SCREEN_W-img.width:
                self.move = -1
            if img.x < 0:
                self.move = 1

        if self.hit:
            self.hit -= 1
            self.fist.y += 6 * self.hit_move

            if self.hit <= 5:
                self.hit_move = -1


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
    game.hit = 10
    game.hit_move = 1
    game.fist.y=game.fist.height/2
    if e.stageX > img.x and e.stageX < img.x+img.width:
        game.sfx['whip'].play()
        game.spin = 20
    else:
        game.sfx['nohit'].play()
    


def flash_main( x=1 ):
    game.init(castToWindow(x))
