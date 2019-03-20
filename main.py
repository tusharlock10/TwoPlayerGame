# import pygame
from socket import *
from threading import Thread
import tj, pickle, sys


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
            data, addr = self.socket.recvfrom(self.buffer)
            variable = pickle.loads(data)
            print(f'Got this: {variable}')
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


if 1:
    print(' * RECEIVER *')
    R = Receiver()
    S = Sender()

    task = Thread(target=R.recv_var, daemon=True)
    task.start()

    for i in range(20):
        data = input('Enter what to send: ')
        S.send_var(data)
        print(f'I have send {data}')

sys.exit()
