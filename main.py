import pygame
from pygame.locals import *
from socket import *
from threading import Thread
import tj
import pickle
import time
import sys

# USER CHANGABLE CONSTANTS
RES = [600, 600]
SIZE = [30, 30]
SIZE_SMALL = [20, 20]
ADDER = 7

PROJ_RADIUS = 5

BG_COLOR = [40, 40, 40]
COLOR_1 = [255, 255, 255]
COLOR_0 = [80, 130, 80]

# AUTO CALCULATED CONSTANTS
ADDER2 = round(ADDER/1.414, 2)
PROJ_MULTI = 1.414


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
        self.__update_center()
        self.player = None  # it is the pygame rectangle object
        self.vel = None
        self.PLAYER_SHOT = False
        self.life = 100

    def __update_center(self):
        self.center = [self.coord[0]+SIZE[0]/2, self.coord[1]+SIZE[1]/2]

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

    def handle_events(self, Proj):  # Proj is the Projectile class here
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
        self.__update_center()
        self.vel = [x_vel, y_vel]

    def add_projectile(self, player_shoots):
        if player_shoots:
            if not self.PLAYER_SHOT:
                # Means Player hits the shoot button, and the shoot button is
                # not already pressed, this approach allows for only 1 shot at a time
                vel = self.vel
                coord = self.center
                Type = self.Type
                Proj.add_projectile(coord, vel, Type)
                self.PLAYER_SHOT = True

        else:
            self.PLAYER_SHOT = False

    def check_died(self):
        if self.life <= 0:
            print(f'Player {self.Type} died!!!')


class Projectile:
    def __init__(self):
        self.projectiles = []

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
        for proj in self.projectiles:
            coord = proj[0]  # Coordinates of the projectile
            vel = proj[1]   # velocity of the projectile
            Type = proj[2]  # Color of the projetile
            if Type:
                color = COLOR_1
            else:
                color = COLOR_0

            new_coord = self.__check_proj_boundary(coord, vel)
            if new_coord and self.check_collision(Player, coord):

                pygame.draw.circle(
                    screen, color, [int(new_coord[0]), int(new_coord[1])], PROJ_RADIUS)

                new_projectiles.append([new_coord, vel, Type])

        self.projectiles = new_projectiles

    def check_collision(self, Player, proj_coord):
        # Here Player is the Player object
        # proj_coord are the coord. of projectile
        if Player.player.collidpoint(proj_coord):
            Player.life -= 15
            return True
        return False

        ### Main Game ###
screen = pygame.display.set_mode(RES)

Clock = pygame.time.Clock()

P = Player(1)
E = Player(0)
Proj = Projectile()


run = True
while run:
    screen.fill(BG_COLOR)

    for e in pygame.event.get():
        if e.type == QUIT:
            run = False
        if e.type == KEYDOWN:
            if e.key == K_ESCAPE:
                run = False

    P.handle_events(Proj)
    P.update_player(screen)
    E.handle_events(Proj)
    E.update_player(screen)
    Proj.draw_proj(screen)

    pygame.display.update()

    Clock.tick(60)
    print(Clock.get_fps())

pygame.quit()
