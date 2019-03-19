import pygame
from socket import *
from threading import Thread
import tj, pickle


class Connection:
    def __init__(self):
        self.my_ip=self.__get_host()    # Get the ip address of this computer
        self.partner_ip=self.__get_partnerhost()
        self.port=8211
        self.addr_to_send=(self.partner_ip, self.port)
        self.addr_me=(self.my_ip, self.port)
        self.buffer=1300

        self.receiver=self.__get_receiversock()
        self.receiver.bind(self.addr_me)    # Binding the receiver to the address

        self.sender=self.__get_sendsock()

        self.message=[False, None]  # contains the data which we got from the partner 

    
    def __get_host(self):
        ip=gethostbyname(gethostname())
        print(f"""IP address of this computer: \
{tj.color_text(str(ip), text_color="BLACK", background_color='WHITE')}""")
        return ip
    
    def __get_partnerhost(self):
        p_ip=input('Enter the ip address of the partner: ')
        return p_ip
    
    def __get_sendsock(self):
        sender = socket(AF_INET, SOCK_DGRAM)
        return sender
    
    def __get_receiversock(self):
        receiver = socket(AF_INET, SOCK_DGRAM)
        return receiver
    
    def send_var(self, variable):
        '''A function to send variables to the partner'''
        data=pickle.dumps(variable)
        self.sender.sendto(data, self.addr_to_send)
        return True

    def recv_var(self):
        '''Run this function in a thread
        This funciton receives a variable from partner'''
        data = self.receiver.recv(self.buffer)
        variable=pickle.loads(data)
        self.message=[True, variable]
        return True

C=Connection()
arg=sys.argv[1:]
if arg=='-r':
    while True:
        C.recv_var()
        data=C.message[1]
        print(data)

else:
    while True:
        data=input('Enter data here: ')
        C.send_var(data)