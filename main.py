import pygame
from pygame.locals import *
from socket import *
from threading import Thread
import tj
import pickle
import time
import sys

# USER CHANGABLE CONSTANTS
RES = [500, 500]
SIZE = [30, 30]
SIZE_SMALL = [20, 20]
ADDER = 7

BG_COLOR = [40, 40, 40]
COLOR_1 = [255, 255, 255]
COLOR_2 = [80, 130, 80]

# AUTO CALCULATED CONSTANTS
ADDER2 = ADDER/1.414
DIFF = [(SIZE[0]-SIZE_SMALL[0])//2, (SIZE[1]-SIZE_SMALL[1])//2]


class Receiver:
    def __init__(self):
        self.my_ip = tj.get_ip_address()  # This PC's IP address
        self.port = 8211
        self.buffer = 1300
        self.my_addr = (self.my_ip, self.port)
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(self.my_addr)
        self.message = [False, None]

    def recv_var(self):
        """Run this function in a thread"""
        while True:
            data, addr = self.socket.recv(self.buffer)
            variable = pickle.loads(data)
            print('Got this: %s' % variable)
            self.message = [True, variable]

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
    def __init__(self, Type):   # Type:1 is me , Type:0 is enemy
        if Type:
            self.controls = {'UP': K_UP, 'DOWN': K_DOWN,
                             'LEFT': K_LEFT, 'RIGHT': K_RIGHT}
            s = [-SIZE[0]*2, -SIZE[1]*2]
            self.color = COLOR_1
        else:
            self.controls = {'UP': K_w, 'DOWN': K_s, 'LEFT': K_a, 'RIGHT': K_d}
            s = [0, 0]
            self.color = COLOR_2

        self.coord = [(RES[0]+s[0])//2, (RES[1]+s[1]) //
                      2]    # Starting coordinates
        self.player = None

    def update_player(self, screen):

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

    def update_velocity(self):
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

        self.coord = self.__check_boundary(self.coord, [x_vel, y_vel])


class Projectile:
    def __init__(self):
        self.projectiles = []

    def add_projectile(self, pos, vel, Type):
        proj = [pos, vel, Type]
        self.projectiles.append(proj)
    
    def draw_proj(self):
        for proj in self.projectiles:




        ### Main Game ###
screen = pygame.display.set_mode(RES)

Clock = pygame.time.Clock()

P = Player(1)
E = Player(0)


run = True
while run:
    screen.fill(BG_COLOR)

    for e in pygame.event.get():
        if e.type == QUIT:
            run = False
        if e.type == KEYDOWN:
            if e.key == K_ESCAPE:
                run = False

    P.update_velocity()
    P.update_player(screen)
    E.update_velocity()
    E.update_player(screen)

    pygame.display.update()

    Clock.tick(60)

pygame.quit()
