#!/bin/env/python
import socket   #for socket
import os
import errno
import sys  #for exit
import time
import json
from myEnum import enum


class TwitterClient:

    def __init__(self, targetHost = '127.0.0.1', portNum = 8000):
        self.username = ''
        self.password = ''
        self.states = enum('LOGIN','CONNECT','LOGGEDIN','SHUTDOWN')
        self.state = self.states.LOGIN
        self.sock = None
        self.host = targetHost
        self.port = portNum
        self.debug = False

        #if flag is passed to script, then output
        #debug messages
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
        self.sock.connect((self.host,self.port))


    def disconnect(self):
        self.sock.close()


    def send_data(self, data):
        try:
            self.sock.sendall(data.encode())
        except OSERROR as e:
            print('ERROR:', e)


    def get_data(self):
        data = self.sock.recv(4096)
        data = data.decode()
        return data


    def get_json(self):
        data = self.sock.recv(4096)
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
            elif self.state == self.states.LOGGEDIN:
                self.handle_LOGGEDIN()
            elif self.state == self.states.SHUTDOWN:
                self.handle_SHUTDOWN()


    #========================================================
    # State Handling Methods 
    #========================================================

    def handle_LOGIN(self):
        print('**************************')
        print('LOGIN')
        print('**************************')
        self.username = input('username:')
        self.password = input('password:')
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

        self.send_data(json.dumps(msg))

        #wait for response from server
        #or wait for timeout
        response = self.get_json()
        
        if self.is_twitter_message(response):
            if response['message_type'] == 'login':
                if self.debug:
                    print('OK: response is a proper twitter message')
                    
                content = response["contents"]

                if content["message"] == 'ok':
                    if self.debug:
                        print('auth accepted, now logging in')
                    self.state = self.states.LOGGEDIN
                    return
                else:
                    if self.debug:
                        print('auth refused: bad login credentials')
            else:
                if self.debug:
                    print('not the right kind of message')
        else:
            if self.debug:
                print('FAIL: response is not a proper twitter message')

        #if we got here, then the credentials werent correct, go back to 
        #login screen
        self.disconnect()
        self.state = self.states.LOGIN



    def handle_LOGGEDIN(self):
        print("Logged In")
        input("type some stuff: ")


    def handle_SHUTDOWN():
        self.sock.close()
        sys.exit()
    #========================================================
    # End State Handling Methods 
    #========================================================

    #check the received json message for the correct fields
    #and sender
    def is_twitter_message(self, json_msg):
        fields = ('sender', 'message_type', 'contents')
        if all (field in json_msg for field in fields):
            if json_msg['sender'] == 'twitter':
                return True
        return False

    #creates a dictionary with basic formatting for messages
    def new_message(self, message_type):
        new_msg = {}
        new_msg["sender"] = self.username 
        new_msg["message_type"] = message_type
        new_msg["contents"] = {"message":''}
        return new_msg



#end of twitter client class 


if __name__ == '__main__':

    twitter_user = TwitterClient()
    twitter_user.run()
