import pygame
from pygame.locals import *
from socket import *
from threading import Thread
import tj
import json
import pickle
import time
import sys
import random
import tj
import zlib

# USER CHANGABLE CONSTANTS

# AQUIRING CONSTANTS ----------------------------------------
D = {
    'RES': [500, 500],
    'SIZE': [40, 40],
    'SIZE_SMALL': [32, 32],
    'ADDER': 6,
    'HIT_POINTS': 5.3,
    'T_SKIP': [1, 1, 1],
    'PROJ_RADIUS': 5,
    'FPS': 60,
    'BG_COLOR': [40, 40, 40],
    'COLOR_1': [255, 205, 220],   # My color
    'COLOR_0': [80, 130, 80],     # Opponent Color
    'FONT': "fc.ttf",
    'WARNING_FONT': "warning.ttf",
    'WARNING_COLOR': [220, 40, 40],
    'SPLASH_TIME': 2,
    'SHOW_WATERMARK': True,
    'WATERMARK_FONT': "watermark.ttf",
    'WATERMARK_COLOR': [48, 48, 48],
    'SHOW_FPS': True}

try:
    f = open('Settings.json', 'r')
    D = json.loads(f.read())
    f.close()
except:
    f = open('Settings.json', 'w')
    f.write(json.dumps(D))
    f.close()

RES = D['RES']
SIZE = D['SIZE']
SIZE_SMALL = D['SIZE_SMALL']
ADDER = D['ADDER']
HIT_POINTS = D['HIT_POINTS']
T_SKIP = D['T_SKIP']
PROJ_RADIUS = D['PROJ_RADIUS']
FPS = D['FPS']
BG_COLOR = D['BG_COLOR']
COLOR_1 = D['COLOR_1']   # My color
COLOR_0 = D['COLOR_0']     # Opponent Color
FONT = D['FONT']
WARNING_FONT = D['WARNING_FONT']
WARNING_COLOR = D['WARNING_COLOR']
SPLASH_TIME = D['SPLASH_TIME']
SHOW_WATERMARK = D['SHOW_WATERMARK']
WATERMARK_COLOR = D['WATERMARK_COLOR']
SHOW_FPS = D['SHOW_FPS']
WATERMARK_FONT = D['WATERMARK_FONT']


# ------------------------------------------------------------------


# AUTO CALCULATED CONSTANTS
TRANSFORMED_COLOR_1 = tj.transform_color(
    COLOR_1, BG_COLOR, skipR=T_SKIP[0], skipG=T_SKIP[1], skipB=T_SKIP[2])
TRANSFORMED_COLOR_0 = tj.transform_color(
    COLOR_0, BG_COLOR, skipR=T_SKIP[0], skipG=T_SKIP[1], skipB=T_SKIP[2])
TRANSFORMED_COLOR_1 = TRANSFORMED_COLOR_1+TRANSFORMED_COLOR_1[::-1]
TRANSFORMED_COLOR_0 = TRANSFORMED_COLOR_0+TRANSFORMED_COLOR_0[::-1]
ADDER2 = round(ADDER/1.414, 2)
PROJ_MULTI = 1.414
SPLASHED = False
temp_splash = 0
time_started = False

DIFF = [(SIZE[0]-SIZE_SMALL[0])//2, (SIZE[1]-SIZE_SMALL[1])//2]
WINNER = None


def cycle(L):   # A simple function to put the first element of the list, at last
    temp = L.pop(0)
    L.append(temp)
    return L


def display_text(screen, text, size, font, color, pos):
    Text = pygame.font.Font(font, size)
    textsurface = Text.render(text, True, color)
    screen.blit(textsurface, pos)


def display_other_info(screen, fps):
    if SHOW_WATERMARK:
        display_text(screen, f"TJ ", 220, WATERMARK_FONT,
                     WATERMARK_COLOR, [RES[0]//2-100, 10])
        display_text(screen, f"Productions", 92, WATERMARK_FONT,
                     WATERMARK_COLOR, [10, RES[1]//3+20])
        display_text(screen, f"2019", 220, WATERMARK_FONT,
                     WATERMARK_COLOR, [50, RES[1]//2])

    if SHOW_FPS:
        fps = round(fps, 1)
        display_text(screen, f"FPS | {fps}", 15, FONT,
                     [200, 200, 200], [RES[0]//2-35, RES[1]-25])


def display_info(screen, Player1, Player0, Proj):
    global SPLASHED, TEMP_SPLASH, time_started, temp_splash
    # Player1,2 and Proj are all objects

    # Firstly, display Health inf of both players
    Life1 = round(Player1.life, 1)
    Life0 = round(Player0.life, 1)
    if Player1.life < 25 and not SPLASHED:
        if not time_started:
            temp_splash = time.time()
            time_started = True

        display_text(screen, f"HEALTH LOW!", RES[0]//5,
                     WARNING_FONT, WARNING_COLOR, [5, RES[1]//2-30])

        if time.time()-temp_splash > SPLASH_TIME:
            SPLASHED = True

    display_text(screen, f"   You   | {Life1} %", 15, FONT, COLOR_1, [10, 10])
    display_text(screen, f"Opponent | {Life0} %", 15, FONT, COLOR_0, [10, 28])

    # Next, display number of live projectiles
    display_text(screen, f"   Your  | {Proj.num_Type1} %",
                 17, FONT, COLOR_1, [RES[0]-130, 10])
    display_text(screen, f"Opponent | {Proj.num_Type0} %",
                 17, FONT, COLOR_0, [RES[0]-130, 28])


class Receiver:
    def __init__(self):
        self.my_ip = tj.get_ip_address()  # This PC's IP address
        self.port = 8211
        self.buffer = 1300
        self.my_addr = (self.my_ip, self.port)
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(self.my_addr)

    def recv_var(self):
        global DATA_RECEIVED
        """Run this function in a thread"""
        while True:
            data = self.socket.recv(self.buffer)
            DATA_RECEIVED = pickle.loads(data)

    def close(self):
        self.socket.close()


class Sender:
    def __init__(self):
        self.partner_ip = self.__get_pip()  # Get IP address of partner (p_ip)
        self.port = 8211
        self.p_addr = (self.partner_ip, self.port)
        self.socket = socket(AF_INET, SOCK_DGRAM)  # Make a UDP socket

    @staticmethod
    def __get_pip():
        ip = tj.get_ip_address()  # input('Enter the IP address of the opponent computer: ')
        return ip

    def send_var(self, variable):
        data = pickle.dumps(variable)
        self.socket.sendto(data, self.p_addr)

    def close(self):
        self.socket.close()


class Player:
    def __init__(self, Type):   # Type: 1 is me , Type: 0 is enemy
        if Type:
            self.controls = {'UP': K_UP, 'DOWN': K_DOWN,
                             'LEFT': K_LEFT, 'RIGHT': K_RIGHT, 'SHOOT': K_SPACE}
            s = [-SIZE[0]*2, -SIZE[1]*2]
            self.color = COLOR_1
        else:
            self.controls = {'UP': K_w, 'DOWN': K_s,
                             'LEFT': K_a, 'RIGHT': K_d, 'SHOOT': K_x}
            s = [0, 0]
            self.color = COLOR_0

        self.Type = Type
        self.coord = [(RES[0]+s[0])//2, (RES[1]+s[1]) //
                      2]    # Coordinates of the upper left corner of the Player
        self.center = None
        self.update_center()
        self.player = None  # it is the pygame rectangle object
        self.vel = None
        self.PLAYER_SHOT = False
        self.life = 100

    def update_center(self):
        self.center = [self.coord[0]+SIZE[0]/2, self.coord[1]+SIZE[1]/2]

    def update_player(self, screen):
        global TRANSFORMED_COLOR_0, TRANSFORMED_COLOR_1
        if self.life < 25:
            if self.Type:
                self.color = TRANSFORMED_COLOR_1[0]
                TRANSFORMED_COLOR_1 = cycle(TRANSFORMED_COLOR_1)
            else:
                self.color = TRANSFORMED_COLOR_0[0]
                TRANSFORMED_COLOR_0 = cycle(TRANSFORMED_COLOR_0)

        self.player = pygame.draw.rect(
            screen, self.color, [int(self.coord[0]), int(self.coord[1]), *SIZE])
        pygame.draw.rect(screen, BG_COLOR,
                         [int(self.coord[0])+DIFF[0], int(self.coord[1])+DIFF[1], *SIZE_SMALL])

    @staticmethod
    def __check_boundary(coord, vel):
        x_vel, y_vel = vel
        x_coord, y_coord = coord

        if y_vel < 0 and 0 <= y_coord-ADDER2-1:
            # Means if player is going UP and player is below the UPPER boundary
            y_coord += y_vel
        elif y_vel > 0 and y_coord <= (RES[1]-SIZE[1]-ADDER2-1):
            # Means if player is going DOWN and player is above the LOWER boundary
            y_coord += y_vel

        if x_vel < 0 and 0 <= x_coord-ADDER2-1:
            # Means if player is going LEFT and player is below the LEFT boundary
            x_coord += x_vel
        elif x_vel > 0 and x_coord <= (RES[0]-SIZE[0]-ADDER2-1):
            # Means if player is going RIGHT and player is above the RIGHT boundary
            x_coord += x_vel

        return [x_coord, y_coord]

    def handle_events(self, Proj):
        global DATA_TO_SEND
        # Proj is the Projectile object here, Sender is the Sender object
        D = pygame.key.get_pressed()

        x_vel, y_vel = 0, 0
        if D[self.controls['UP']]:
            y_vel = -ADDER
        elif D[self.controls['DOWN']]:
            y_vel = ADDER

        if D[self.controls['LEFT']]:
            if y_vel < 0:
                x_vel = -ADDER2
                y_vel = -ADDER2
            elif y_vel > 0:
                x_vel = -ADDER2
                y_vel = ADDER2
            else:
                x_vel = -ADDER

        elif D[self.controls['RIGHT']]:
            if y_vel < 0:
                x_vel = ADDER2
                y_vel = -ADDER2
            elif y_vel > 0:
                x_vel = ADDER2
                y_vel = ADDER2
            else:
                x_vel = ADDER

        if D[self.controls['SHOOT']]:
            player_shoots = True
        else:
            player_shoots = False
        self.add_projectile(player_shoots)

        self.coord = self.__check_boundary(self.coord, [x_vel, y_vel])
        DATA_TO_SEND.append(self.coord)

        self.update_center()
        self.vel = [x_vel, y_vel]

    def add_projectile(self, player_shoots):
        global Proj
        if player_shoots:
            if not self.PLAYER_SHOT:
                # Means Player hits the shoot button, and the shoot button is
                # not already pressed, this approach allows for only 1 shot at a time
                vel = self.vel
                coord = self.center
                Type = self.Type
                proj = [coord, vel, Type]
                Proj.add_projectile(coord, vel, Type)
                DATA_TO_SEND.append(proj)
                self.PLAYER_SHOT = True

        else:
            self.PLAYER_SHOT = False

    def check_died(self):
        if self.life <= 0:
            print(f'Player {self.Type} died!!!')


class Projectile:
    def __init__(self):
        self.projectiles = []
        self.num_Type1, self.num_Type0 = 0, 0

    def add_projectile(self, coord, vel, Type):
        proj = [coord, vel, Type]
        self.projectiles.append(proj)

    @staticmethod
    def __check_proj_boundary(coord, vel):
        """Check if the projectile is in the boundary or not
        If it is in the boundary, then return updated coordinates
        Else return None, as a signal to destroy that projectile"""
        x_vel, y_vel = vel
        x_vel, y_vel = x_vel*PROJ_MULTI, y_vel*PROJ_MULTI
        x_coord, y_coord = coord

        if y_vel < 0 and 0 <= y_coord:
            # Means if proj is going UP and player is below the UPPER boundary
            y_coord += y_vel
        elif y_vel > 0 and y_coord <= RES[1]:
            # Means if proj is going DOWN and player is above the LOWER boundary
            y_coord += y_vel

        if x_vel < 0 and 0 <= x_coord:
            # Means if proj is going LEFT and player is below the LEFT boundary
            x_coord += x_vel
        elif x_vel > 0 and x_coord <= RES[0]:
            # Means if proj is going RIGHT and player is above the RIGHT boundary
            x_coord += x_vel

        new_coord = [x_coord, y_coord]
        if new_coord != coord:
            return new_coord
        else:
            return None

    def draw_proj(self, screen, Player1, Player2):
        new_projectiles = []
        self.num_Type1, self.num_Type0 = 0, 0
        for proj in self.projectiles:
            coord = proj[0]  # Coordinates of the projectile
            vel = proj[1]   # velocity of the projectile
            Type = proj[2]  # Color of the projetile
            to_not_draw = False

            if Type:    # Means is Type: 1, means projectile is fired by player 1
                color = COLOR_1
            else:
                color = COLOR_0

            new_coord = self.__check_proj_boundary(coord, vel)
            if new_coord:
                if Type != Player1.Type:
                    # That is, if the projectile and player type is different
                    to_not_draw = self.check_collision(Player1, coord)
                elif Type != Player2.Type:
                    # That is, if the projectile and player type is different
                    to_not_draw = self.check_collision(Player2, coord)

                if not to_not_draw:
                    pygame.draw.circle(
                        screen, color, [int(new_coord[0]), int(new_coord[1])], PROJ_RADIUS)
                    new_projectiles.append([new_coord, vel, Type])

                    if Type:
                        self.num_Type1 += 1
                    else:
                        self.num_Type0 += 1

        self.projectiles = new_projectiles

    def check_collision(self, Player, proj_coord):
        # Here Player is the Player object
        # proj_coord are the coord. of projectile
        if Player.player.collidepoint(proj_coord):
            Player.life -= HIT_POINTS
            if Player.life < 0:
                Player.life = 0
            return True
        return False


def handle_enemy():
    # This is the function, specifically for handeling the enemy
    global DATA_RECEIVED, E, Proj
    coord = DATA_RECEIVED[0]
    proj = DATA_RECEIVED[1]
    E.coord = coord
    E.update_center()
    Proj.add_projectile(proj[0], proj[1], 0)

    ### Main Game ###


pygame.init()       # Initialize modules
pygame.font.init()

screen = pygame.display.set_mode(RES)
Clock = pygame.time.Clock()

R = Receiver()
task = Thread(target=R.recv_var, daemon=True)
task.start()
S = Sender()


P = Player(1)
E = Player(0)
Proj = Projectile()


run = True
while run:
    DATA_TO_SEND = []
    DATA_RECEIVED = []
    screen.fill(BG_COLOR)

    for e in pygame.event.get():
        if e.type == QUIT:
            run = False
        if e.type == KEYDOWN:
            if e.key == K_ESCAPE:
                run = False

    display_other_info(screen, Clock.get_fps())
    Proj.draw_proj(screen, P, E)
    P.handle_events(Proj)
    P.update_player(screen)
    E.handle_events(Proj)
    E.update_player(screen)

    P.check_died()
    E.check_died()
    display_info(screen, P, E, Proj)

    S.send_var(DATA_TO_SEND)

    pygame.display.update()

    Clock.tick(FPS)

pygame.quit()
