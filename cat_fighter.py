import pygame
from pygame.locals import *
import sys
import time
import pyganim
import random
import urllib2
import eztext

icon = pygame.image.load('resources/icon.bmp')
pygame.display.set_icon(icon)

pygame.init()
pygame.mixer.init()

meow = pygame.mixer.Sound('resources/meow.wav')
grunt = pygame.mixer.Sound('resources/grunt.wav')

pygame.mixer.music.load('resources/sigil.ogg')
pygame.mixer.music.play(-1)


txtbx = eztext.Input(maxlength=45, color=(0,0,0), prompt='Name: ')

WIDTH = 640
HEIGHT = 480
CAT_SPAWN_RATE = 200
CAT_DAMAGE = 20
CAT_SPEED = 2
CAT_JUMP_SPEED = 15
PLAYER_SPEED = 5
PLAYER_JUMP_SPEED = 16

# set up the window
windowSurface = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('How many cats can John fight')
flags = windowSurface.get_flags()

# set up background
background = pygame.image.load("resources/background.png")

loading_screen = pygame.image.load("resources/loading_screen.png")
loading_screen = loading_screen.convert()

# global variables
floor = 440
gravity = 0.6
time = 0
score = 0
state = 0
diff = "Easy"
success = 0
name = " "
# sprite container

all_sprites_list = pygame.sprite.LayeredDirty()
all_sprites_list.clear(windowSurface, background)

cat_set = set([])
attacks = pygame.sprite.Group()

def toggle_fullscreen():
    global flags
    if flags&FULLSCREEN==False:
        flags|=FULLSCREEN
        pygame.display.set_mode((WIDTH,HEIGHT), flags)
    else:
        flags^=FULLSCREEN
        pygame.display.set_mode((WIDTH,HEIGHT), flags)

def new_game():
    global score, cat_set, all_sprites_list, state, success
    score = 0
    player.health = 100
    player.pos = [WIDTH/2, floor - player.height]
    player.vel = [0,0]
    player.dead = False
    player.anim = player.animation_set['idle']
    for cat in set(cat_set):
        cat.kill()
    cat_set = set([])
    state = 1
    success = 0

def set_easy():
    global CAT_SPAWN_RATE, CAT_DAMAGE, CAT_SPEED, CAT_JUMP_SPEED, diff
    CAT_SPAWN_RATE = 200
    CAT_DAMAGE = 20
    CAT_SPEED = 2
    CAT_JUMP_SPEED = 15
    diff = "Easy"

def set_normal():
    global CAT_SPAWN_RATE, CAT_DAMAGE, CAT_SPEED, CAT_JUMP_SPEED, diff
    CAT_SPAWN_RATE = 60
    CAT_DAMAGE = 25
    CAT_SPEED = 3
    CAT_JUMP_SPEED = 18
    diff="Normal"

def set_insane():
    global CAT_SPAWN_RATE, CAT_DAMAGE, CAT_SPEED, CAT_JUMP_SPEED, diff
    CAT_SPAWN_RATE = 30
    CAT_DAMAGE = 50
    CAT_SPEED = 6
    CAT_JUMP_SPEED = 20
    diff = "Insane"
# sprite sheet import helper function
def sprite_builder(size,file,speed,loop = True, pos=(0,0)):

    #Initial Values
    len_sprt_x,len_sprt_y = size #sprite size
    sprt_rect_x,sprt_rect_y = pos #where to find first sprite on sheet

    sheet = pygame.image.load(file).convert_alpha() #Load the sheet
    sheet_rect = sheet.get_rect()
    sprites = []
    for i in range(0,sheet_rect.height-len_sprt_y,size[1]):#rows
        for i in range(0,sheet_rect.width-len_sprt_x,size[0]):#columns
            sheet.set_clip(pygame.Rect(sprt_rect_x, sprt_rect_y, len_sprt_x, len_sprt_y)) #find sprite you want
            sprite = sheet.subsurface(sheet.get_clip()) #grab the sprite you want
            sprites.append(sprite)
            sprt_rect_x += len_sprt_x

        sprt_rect_y += len_sprt_y
        sprt_rect_x = 0
    sprites_out = []
    for i in sprites:
        sprites_out.append([i, speed])
    anim_out = pyganim.PygAnimation(sprites_out, loop)
    return anim_out

# load spritesheets	
idleAnim = sprite_builder([85,159], "resources/ryu_idle.png", 0.2)
punchAnim = sprite_builder([140,169], "resources/ryu_punch.png", 0.1)
jumpAnim = sprite_builder([90,194], "resources/ryu_jump.png", 0.15)
crouchAnim = sprite_builder([85,159], "resources/ryu_crouch.png", 0.35)
kickAnim = sprite_builder([180,159], "resources/ryu_kick.png", 0.13)
deadAnim = sprite_builder([150, 123], "resources/ryu_dead.png", 0.3, False)
hurtAnim = sprite_builder([104, 159], 'resources/ryu_hurt.png', 0.2)


catwalkAnim = sprite_builder([88,81], "resources/cat_walk.png", 0.1)
catdeadAnim = sprite_builder([88,81], "resources/cat_dead.png", 0.1)


# set animations
idleAnim.play()
punchAnim.play()
jumpAnim.play()
crouchAnim.play()
kickAnim.play()
hurtAnim.play()

catwalkAnim.play()
catdeadAnim.play()


ryu_anim = {'idle': idleAnim, 'crouch': crouchAnim, 'punch': punchAnim, 'jump': jumpAnim, 'kick': kickAnim, 'dead': deadAnim, 'hurt': hurtAnim}
cat_anim = {'idle': catwalkAnim, 'jump': catwalkAnim, 'dead': catdeadAnim}

class Creature(pygame.sprite.DirtySprite):
    def __init__(self, init_health, init_pos, vel, acc, jump_speed, standing, height, face_left, animation_set):
        pygame.sprite.DirtySprite.__init__(self)
        self.health = init_health
        self.pos = init_pos
        self.height = height
        self.pos[1] -= self.height
        self.vel = vel
        self.acc = acc
        self.jump_speed = jump_speed
        self.standing = standing
        self.anim_time = float('inf')
        self.face_left = face_left
        self.dirty = 2
        self.animation_set = animation_set
        self.anim = self.animation_set['idle']
        self.image = self.anim.getCurrentFrame()
        self.rect = self.anim.getRect()
        self.mask = pygame.mask.from_surface(self.image)
        self.dead = False
        

    def jump(self):
        if self.standing:
            self.vel[1] -= self.jump_speed
            self.standing = False

    
    def update(self):
        self.image = self.anim.getCurrentFrame()
        if not self.face_left:
            self.image = pygame.transform.flip(self.image, True, False)
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = self.pos[0]
        self.rect.y = self.pos[1]
 
        for i in range(2):
            self.pos[i] += self.vel[i]
        
        if not self.standing:
            if not self.dead:
                self.anim = self.animation_set['jump']
            self.vel[1] += gravity
            if self.pos[1] >= floor - self.height:
                self.standing = True
                self.vel[1] = 0
                self.pos[1] = floor - self.height
                if not self.dead:
                    self.anim = self.animation_set['idle']

        self.anim_time -=1
        if self.anim_time == 0:
            self.anim = self.animation_set['idle']
            self.anim_time = float('inf')

            
class Player(Creature):
    def __init__(self, init_health, init_pos, vel, acc, jump_speed, standing, height, face_left, animation_set):
        Creature.__init__(self, init_health, init_pos, vel, acc, jump_speed, standing, height, face_left, animation_set)
        self.hurt = False
        self.hurt_counter = float('inf')
        self.dead_timer = float('inf')
         
    def left(self):
        self.face_left = True
        self.vel[0] -= self.acc

    def right(self):
        self.face_left = False
        self.vel[0] += self.acc
        
    def stop_left(self):
        self.vel[0] += self.acc

    def stop_right(self):
        self.vel[0] -= self.acc

    def down(self):
        self.anim = self.animation_set['crouch']

    def up(self):
        self.anim = self.animation_set['idle']

    def punch(self):
        global punches
        if self.standing:
            self.anim = self.animation_set['punch']
            self.anim_time = 30

            attacks.add(Punch(self.face_left))

    def kick(self):
        global kicks
        if self.standing:
            self.anim = self.animation_set['kick']
            self.anim_time = 30

            attacks.add(Kick(self.face_left))

    def die(self):
        self.anim = self.animation_set['dead']
        self.anim_time = float('inf')
        deadAnim.play()
        self.dead_timer = 40
    
    def update(self):
        global state
        Creature.update(self)
        if self.pos[0] < -20:
            self.pos[0] = -20
        elif self.pos[0] > WIDTH - 50:
            self.pos[0] = WIDTH - 50
        self.hurt_counter -= 1
        if self.hurt_counter == 0:
            self.hurt = False
            self.hurt_counter = float('inf')
        if self.health == 0:
            self.vel[0] = 0
            self.dead = True
            self.die()
            self.health = -1
        self.dead_timer -= 1
        if self.dead_timer == 0:
            state = 2



# create player and add to sprites list
player = Player(100, [WIDTH/2,floor], [0,0], PLAYER_SPEED, PLAYER_JUMP_SPEED, True, 159, True, ryu_anim)

all_sprites_list.add(player)

# cat class
class Cat(Creature):
    def __init__(self, init_health, init_pos, vel, acc, jump_speed, standing, height, face_left, animation_set):
        Creature.__init__(self,init_health,  init_pos, vel, acc, jump_speed, standing, height, face_left, animation_set)
        self.bounced = False
        self.bounce_timer = float('inf')
        self.death_timer = float('inf')
        
    def find_player(self):
        if player.pos[0] + player.rect.width > self.pos[0] + self.rect.width:
            self.face_left = False
            self.vel[0] = self.acc
        else:
            self.face_left = True
            self.vel[0] = -self.acc

    def bounce(self):
        if self.pos[0] < player.pos[0]:
            self.vel[0] = -3
        else:
            self.vel[0] = 3
        self.bounced = True
        self.bounce_timer = 30
        self.jump()

    def die(self):
        meow.play()
        cat_set.remove(self)
        self.vel = [0,0]
        self.bounce()
        self.dead = True
        self.death_timer = 60
        self.anim = self.animation_set['dead']
            
    def update(self):
        if not (self.bounced or self.dead or player.dead):
            self.find_player()
            if random.random() > 0.991:
                self.jump()
        Creature.update(self)
        self.bounce_timer -= 1
        if self.bounce_timer == 0:
            self.bounced = False
        self.death_timer -=1
        if self.death_timer == 0:
            self.kill()
        

class Punch(pygame.sprite.Sprite):
    def __init__(self, orient):
        pygame.sprite.Sprite.__init__(self)
        self.face_left = orient
        if self.face_left:
            self.rect = pygame.Rect(player.pos[0] - 3, player.pos[1] - 10, 20, 30)
        else:
            self.rect = pygame.Rect(player.pos[0] + 71, player.pos[1] - 10, 71, 30)
        self.punch_time = 30

    def update(self):
        if player.anim == player.animation_set['punch'] and player.face_left:
            self.rect = pygame.Rect(player.pos[0] - 3, player.pos[1] - 10, 20, 30)
        elif player.anim == player.animation_set['punch']:
            self.rect = pygame.Rect(player.pos[0] + 71, player.pos[1] - 10, 71, 30)
        self.punch_time -= 1
        if self.punch_time == 0:
            self.kill()

class Kick(pygame.sprite.Sprite):
    def __init__(self, orient):
        pygame.sprite.Sprite.__init__(self)
        self.face_left = orient
        if self.face_left:
            self.rect = pygame.Rect(player.rect.x, floor - 30, 90, 40)
        else:
            self.rect = pygame.Rect(player.rect.x + 90, floor - 30, 90, 40)
        self.kick_time = 30

    def update(self):
        if player.anim == player.animation_set['kick'] and player.face_left:
            self.rect = pygame.Rect(player.rect.x, floor - 30, 90, 40)
        elif player.anim == player.animation_set['kick']:
            self.rect = pygame.Rect(player.rect.x + 90, floor - 30, 90, 40)
        self.kick_time -= 1
        if self.kick_time == 0:
            self.kill()

class Score(pygame.sprite.DirtySprite):
    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)
        self.basicFont = pygame.font.SysFont(None, 48)
        self.image = self.basicFont.render("Score: " + str(score), 1, (255, 255, 255))
        self.rect = self.image.get_rect()
        self.rect.centerx = 500
        self.rect.centery = 50
        self.dirty = 1

    def update(self):
        self.image = self.basicFont.render("Score: " + str(score), 1, (255, 255, 255))


st = Score()
all_sprites_list.add(st)

class HealthBar(pygame.sprite.DirtySprite):
    def __init__(self):
        pygame.sprite.DirtySprite.__init__(self)
        self.font = pygame.font.SysFont(None, 36)
        txt = self.font.render("Health:", 1, (255, 255, 255))
        image = pygame.Surface((200,200), pygame.SRCALPHA, 32)
        image = image.convert_alpha()
        image.blit(txt, (0,0))
        pygame.draw.rect(image, (0,0,0), [30, 30, 50 ,50 ], 5)
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.x = 30
        self.rect.y = 30
        self.dirty = 1

    def update(self):
        image = pygame.Surface((200,200), pygame.SRCALPHA, 32)
        image = image.convert_alpha()
        txt = self.font.render("Health", 1, (255, 255, 255))
        image.blit(txt, (0,0))
        pygame.draw.rect(image, (0,0,0), [25, 30, 110 , 40 ], 1)
        pygame.draw.rect(image, (252, 105, 32), [30, 35, player.health, 30])
        self.image = image

hb = HealthBar()
all_sprites_list.add(hb)
# standard keyboard commands

keydowns = {276: player.left, 275:player.right, 273: player.jump, 274:player.down, 122: player.punch, 120: player.kick, 282: toggle_fullscreen}
keyups = {276: player.stop_left, 275:player.stop_right, 274: player.up}

# key handlers

def keydown_handler(key):
    for i in keydowns.keys():
        if key == i:
            keydowns[i]()
            
def keyup_handler(key):
    for i in keyups.keys():
        if key == i:
            keyups[i]()

def cat_spawn():
    cat = Cat(20, [random.choice([0,WIDTH]),floor], [0,0], CAT_SPEED, CAT_JUMP_SPEED, True, 82, False, cat_anim)
    cat_set.add(cat)
    all_sprites_list.add(cat)

def check_collisions():
    global score
    for attack in attacks:
        attack.update()
        for cat in set(cat_set):
            if attack.rect.colliderect(cat.rect):
                offset_x, offset_y = (cat.rect.left - player.rect.left), (cat.rect.top - player.rect.top)
                if player.mask.overlap(cat.mask, [offset_x, offset_y]):
                    cat.die()
                    score+=1
                    st.dirty = 1
    for cat in set(cat_set):
        if cat.alive() and player.rect.colliderect(cat.rect) and not player.hurt:
            offset_x, offset_y = (cat.rect.left - player.rect.left), (cat.rect.top - player.rect.top)
            if player.mask.overlap(cat.mask, [offset_x, offset_y]):
                cat.bounce()
                if not player.dead:
                    grunt.play()
                    player.anim = player.animation_set['hurt']
                    player.anim_time = 25
                    player.hurt = True
                    player.hurt_counter = 30
                    player.health -= CAT_DAMAGE
                    hb.dirty = 1


mainClock = pygame.time.Clock()


def main_loop():
    global state, time, score, success, name
    if state == 0:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == 282:
                toggle_fullscreen()
            elif event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                if 57 < pos[0] < 208 and 284 < pos[1] < 372:
                    set_easy()
                    new_game()
                elif 245 < pos[0] < 396 and 284 < pos[1] < 372:
                    set_normal()
                    new_game()
                elif 442 < pos[0] < 592 and 284 < pos[1] < 372:
                    set_insane()
                    new_game()
        windowSurface.blit(loading_screen, (0,0))
        basicFont = pygame.font.SysFont(None, 44)
        successhighscore = basicFont.render("High Score Sent", 1, (0,0, 0))
        failhighscore = basicFont.render("High Score Failed", 1, (0,0, 0))
        if success == 1:
            windowSurface.blit(successhighscore, (100, 5))
        elif success == 2:
            windowSurface.blit(failhighscore, (100, 5))
        pygame.display.update()
    if state == 1:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if not player.dead:
                    keydown_handler(event.key)
            if event.type == KEYUP:
                if not player.dead:
                    keyup_handler(event.key)
                
        for i in all_sprites_list:
            i.update()

        check_collisions()
        
        rects = all_sprites_list.draw(windowSurface)
        pygame.display.update(rects)

        if time % CAT_SPAWN_RATE == 0:
            cat_spawn()
        time += 1

    if state == 2:
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == 121:
                state = 3
                name=" "
            elif event.type == KEYDOWN and event.key == 13:
                state = 0
        basicFont = pygame.font.SysFont(None, 38)
        GOFont = pygame.font.SysFont(None, 80)
        GO = GOFont.render("GAME OVER", 1, (255, 255, 255))
        again = basicFont.render("Press y to save high score or enter to start again", 1, (255,255, 255))
        windowSurface.blit(GO, (WIDTH/2 - 170, HEIGHT/2 - 80))
        windowSurface.blit(again, (0, HEIGHT/2))
        pygame.display.update()

    if state == 3:
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN and event.key == 13:
                name = txtbx.update(events)
                if name == " " or name == "":
                    name = "ANON"
                try:
                    sendhighscore = urllib2.urlopen("http://highscores.bal-do.net/db2.php?g=" + diff + "&n=" + name +"&s=" + str(score)).read()
                    success = 1
                except Exception as e:
                    print e
                    success = 2
                state = 0
          
        windowSurface.fill((255,255,255))
        basicFont = pygame.font.SysFont(None, 44)
        instruction = basicFont.render("Type in your name and press enter to send", 1, (0,0,0))
        plug = basicFont.render("See high scores at bal-do.net", 1, (0,0,0))
        windowSurface.blit(instruction, (0, HEIGHT/2 - 50))
        windowSurface.blit(plug, (0, HEIGHT/2 + 30))
        txtbx.update(events)
        txtbx.draw(windowSurface)
        pygame.display.update()
    mainClock.tick(60)

while True:
    main_loop()


