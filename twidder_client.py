#!/bin/env/python
import socket
import os
import errno
import sys
import signal
import time
import json
from getpass import getpass
from myEnum import enum

#signal handler for ctrl-c (SIGINT)
def sigint_handler(signal, fram):
    print('\nClosing client...\n')
    sys.exit(0)
signal.signal(signal.SIGINT,sigint_handler)


class TwitterClient:

    def __init__(self, targetHost = '127.0.0.1', portNum = 8000):
        self.username = ''
        self.password = ''
        self.states = enum('LOGIN','CONNECT','MAIN_MENU','OFFLINE_MESSAGES','EDIT_SUBSCRIPTIONS','NEW_POST','HASHTAG_SEARCH','LOGOUT')
        self.state = self.states.LOGIN
        self.sock = None
        self.host = targetHost
        self.port = portNum
        self.debug = False

        #if flag is passed to script, then output
        #debug messages
        if len(sys.argv) > 1:
            if sys.argv[1] == 'd':
                self.debug = True


    def set_target_host(self, h = '127.0.0.1'):
        self.host = h


    def set_target_host(self, p = 8000):
        self.port = p


    def set_socket_blocking(self, on = True):
        if self.sock == None:
            print('ERROR: no socket found')
            return None
        self.sock.setblocking(on)


    def set_socket_timeout(self, timeout = 10):
        if self.sock == None:
            print('ERROR: no socket found')
            return None
        self.sock.settimeout(timeout)


    def get_socket(self):
        # try to create a socket, if creation of socket fails, then simply
        # kill the client
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except OSError as e:
            print("ERROR:",e)
            sys.exit()


    def connect(self):
        self.get_socket()
        try:
            self.sock.connect((self.host,self.port))
        except:
            print('connection refused')
            sys.exit()


    def disconnect(self):
        self.sock.close()


    def send_data(self, data):
        try:
            self.sock.sendall(data.encode())
        except OSError as e:
            print('ERROR:',e)


    def get_data(self):
        try:
            data = self.sock.recv(4096)
        except OSError as e:
            print("ERROR:",e)
        data = data.decode()
        return data


    def get_json(self):
        try:
            data = self.sock.recv(4096)
        except OSError as e:
            print('ERROR:',e)

        if self.debug:
            print('data before decode:',data)
        data = data.decode()
        if self.debug:
            print('data after decode:')
            print(json.dumps(data,indent=4))
        try:
            json_data = json.loads(data)
        except:
            print('ERROR: failed to load json (is the message proper JSON?)')

        if self.debug:
            print('received json data:')
            print(json.dumps(json_data, indent=4))

        return json_data


    def run(self):
        while True:
            if self.state == self.states.LOGIN:
                self.handle_LOGIN()
            elif self.state == self.states.CONNECT:
                self.handle_CONNECT()
            elif self.state == self.states.MAIN_MENU:
                self.handle_MAIN_MENU()
            elif self.state == self.states.OFFLINE_MESSAGES:
                self.handle_OFFLINE()
            elif self.state == self.states.EDIT_SUBSCRIPTIONS:
                self.handle_SUBSCRIPTIONS()
            elif self.state == self.states.NEW_POST:
                self.handle_POST()
            elif self.state == self.states.HASHTAG_SEARCH:
                self.handle_SEARCH()
            elif self.state == self.states.LOGOUT:
                self.handle_LOGOUT()


    #========================================================
    # State Handling Methods 
    #========================================================

    def handle_LOGIN(self):
        os.system('clear')
        print('**************************')
        print('Twidder Login')
        print('**************************')
        self.username = input('username:').strip()
        self.password = getpass('password:')
        self.state = self.states.CONNECT


    #handle client's initial connection to the server
    def handle_CONNECT(self):
        if self.debug:
            print("connecting to server...")

        #connect to remote host at self.host
        #through its target port self.port
        self.connect()

        #will send a json string to server
        msg = self.new_message(message_type = 'login')
        msg['contents']['message'] = {  "username":self.username,
                                        "password":self.password}

        #send the json object encoded as a string
        if self.debug:
            print("sending credentials to server")
            print(json.dumps(msg,indent=4))

        #send connection request to server
        self.send_data(json.dumps(msg))

        #wait for response from server
        #or wait for timeout
        response = self.get_json()
        
        if self.is_twidder_message(response):
            if response['message_type'] == 'login':
                if self.debug:
                    print('OK: response is a proper twidder message')
                    
                content = response["contents"]

                if content["message"] == 'ok':
                    if self.debug:
                        print('auth accepted, now logging in')
                    self.state = self.states.MAIN_MENU
                    return
                else:
                    if self.debug:
                        print('auth refused: bad login credentials')
                    print('Invalid login (did you enter the correct username and password?)')
                    input('press enter to continue')
            else:
                if self.debug:
                    print('not the right kind of message')
        else:
            if self.debug:
                print('FAIL: response is not a proper twidder message')

        #if we got here, then the credentials werent correct, go back to 
        #login screen
        self.disconnect()
        self.state = self.states.LOGIN


    def handle_MAIN_MENU(self):
        print("Logged In")
        choice = self.print_menu()
        print("you chose",choice)
        
        #based on input, decide which state to go to
        if choice == 1:
            self.state = self.states.OFFLINE_MESSAGES
        elif choice == 2:
            self.state = self.states.EDIT_SUBSCRIPTIONS
        elif choice == 3:
            self.state = self.states.NEW_POST
        elif choice == 4:
            self.state = self.states.HASHTAG_SEARCH
        elif choice == 5:
            self.state = self.states.LOGOUT


    def handle_OFFLINE(self):
        os.system('clear')
        print('***************************')
        print('Offline Messages')
        print('***************************')
        print('view offline messages')

        #TODO: build offline message request
        #send connection request to server
        self.send_data(json.dumps(msg))
        choice = input('push enter to go back to main')
        self.state = self.states.MAIN_MENU


    def handle_SUBSCRIPTIONS(self):
        os.system('clear')
        print('***************************')
        print('Your Subscriptions')
        print('***************************')
        choice = input('push enter to go back to main')
        self.state = self.states.MAIN_MENU


    def handle_POST(self):
        os.system('clear')
        print('***************************')
        print('New Post')
        print('***************************')
        choice = input('push enter to go back to main')
        self.state = self.states.MAIN_MENU


    def handle_SEARCH(self):
        os.system('clear')
        print('***************************')
        print('Hashtag Search')
        print('***************************')
        choice = input('push enter to go back to main')
        self.state = self.states.MAIN_MENU


    def handle_LOGOUT(self):
        print('Closing client...')
        self.sock.close()
        sys.exit()
    #========================================================
    # End State Handling Methods 
    #========================================================

    #check the received json message for the correct fields
    #and sender
    def is_twidder_message(self, json_msg):
        fields = ('sender', 'message_type', 'contents')
        if all (field in json_msg for field in fields):
            if json_msg['sender'] == 'twidder':
                return True
        return False

    #creates a dictionary with basic formatting for messages
    def new_message(self, message_type):
        new_msg = {}
        new_msg["sender"] = self.username 
        new_msg["message_type"] = message_type
        new_msg["contents"] = {"message":''}
        return new_msg


    def print_menu(self):
        os.system('clear')
        menu =  '***************************\n'
        menu += 'Welcome ' + self.username + '\n'
        menu += '***************************\n'
        menu += '1 - See offline messages\n'
        menu += '2 - Edit subscriptions\n'
        menu += '3 - Make a post\n'
        menu += '4 - Hashtag search\n'
        menu += '5 - Logout\n'
        menu += '****************************'

        choice = 0
        while choice < 1 or choice > 5:
            print(menu)
            choice = input('enter choice: ')
            if choice.isnumeric():
                choice = int(choice)
            else:
                return 0
        if self.debug:
            print('choice is valid!')
        return choice
#end of twidder client class 


if __name__ == '__main__':

    twidder_user = TwitterClient()
    twidder_user.run()
