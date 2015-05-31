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

class TwidderClient:

    def __init__(self, targetHost = '127.0.0.1', portNum = 8000):
        self.username = ''
        self.password = ''
        self.states = enum('LOGIN','CONNECT','MAIN_MENU',
                           'OFFLINE_MAIN', 'OFFLINE_ALL', 'OFFLINE_SUBSCRIPTIONS',
                           'SUBSCRIPTIONS_MAIN','SUBSCRIPTIONS_ADD','SUBSCRIPTIONS_DELETE',
                           'NEW_POST',
                           'HASHTAG_SEARCH',
                           'LOGOUT'
                           )
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

            elif self.state == self.states.OFFLINE_MAIN:
                self.handle_OFFLINE_MAIN()

            elif self.state == self.states.OFFLINE_ALL:
                self.handle_OFFLINE_ALL()

            elif self.state == self.states.OFFLINE_SUBSCRIPTIONS:
                self.handle_OFFLINE_SUBSCRIPTIONS()

            elif self.state == self.states.SUBSCRIPTIONS_MAIN:
                self.handle_SUBSCRIPTIONS_MAIN()

            elif self.state == self.states.SUBSCRIPTIONS_ADD:
                self.handle_SUBSCRIPTIONS_ADD()

            elif self.state == self.states.SUBSCRIPTIONS_DELETE:
                self.handle_SUBSCRIPTIONS_DELETE()

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
        choice = self.print_main_menu()
        
        #based on input, decide which state to go to
        if choice == 1:
            self.state = self.states.OFFLINE_MAIN
        elif choice == 2:
            self.state = self.states.SUBSCRIPTIONS_MAIN
        elif choice == 3:
            self.state = self.states.NEW_POST
        elif choice == 4:
            self.state = self.states.HASHTAG_SEARCH
        elif choice == 5:
            self.state = self.states.LOGOUT


    def handle_OFFLINE_MAIN(self):
        choice = self.print_offline_menu_main()
        if choice == 1:
          self.state = self.states.OFFLINE_ALL
        if choice == 2:
          self.state = self.states.OFFLINE_SUBSCRIPTIONS
        if choice == 3:
          self.state = self.states.MAIN_MENU

    def handle_OFFLINE_ALL(self):
        os.system('clear')
        print('***************************')
        print('All Offline Messages')
        print('***************************\n')

        #build request and send to server
        msg = self.new_message(message_type = 'offline_messages')
        msg['contents']['message'] = 'all_unread'
        self.send_data(json.dumps(msg))
        
        #wait for response from server
        response = self.get_json()

        #if there are no missed messages, the message is None
        if response['contents']['message'] == None:
          print('No missed posts')
          print('Looks like your all up to date :D\n')
        else:
          #the response contains all the missed messages, along with the subscription
          #the messages are associated with
          all_messages = response['contents']['message']
          for user in all_messages:
            print('-----------------------------------------------------')
            print('Missed posts from', user[0][0]) #this gets the name of the user (wierd structure :/)
            print('-----------------------------------------------------')
            for msg in user:
              print(msg[0],'posted:',msg[1])
            print('-----------------------------------------------------\n\n')

        
        choice = input('**push enter to go back**')
        self.state = self.states.OFFLINE_MAIN


    def handle_OFFLINE_SUBSCRIPTIONS(self):
        #build request and send to server
        #request a list of subscriptions
        msg = self.new_message(message_type = 'offline_messages')
        msg['contents']['message'] = 'get_subscriptions'
        self.send_data(json.dumps(msg))
        
        #wait for response from server
        response = self.get_json()
        subscriptions = response['contents']['message']
        if len(subscriptions) == 0:
          print('You have no subscriptions')
          choice = input('**push enter to go back**')
          self.state = self.states.OFFLINE_MAIN
        else:
          choice = self.subscription_menu('Missed Messages by Subscription',subscriptions) 
          if choice == len(subscriptions):
            self.state = self.states.OFFLINE_MAIN
          elif choice == None:
            self.state = self.states.OFFLINE_SUBSCRIPTIONS
          else:
            print("you chose subscription",choice+1,"-",subscriptions[choice])
            #I now have the user_id of the subscription, now request messages for this subscription
            #from the server and display those messages

            #user id of this particular subscription leader
            subscription = subscriptions[choice]

            #request messages from this subscription 
            msg = self.new_message(message_type = 'offline_messages')
            msg['contents']['message'] = 'unread_from_subscription'
            msg['contents']['leader_id'] = subscriptions[choice]
            self.send_data(json.dumps(msg))
            
            #wait for response from server
            response = self.get_json()
            messages = response['contents']['message']

            os.system('clear')
            print('***************************')
            print('Missed Message From:',subscription)
            print('***************************\n')

            #if there are no missed messages for this subscription
            #just say so
            if len(messages) <= 0:
              print('No missed posts')
              print('Looks like your all up to date :D\n')
            else:
              #the response contains all the missed messages, along with the subscription
              #the messages are associated with
              for msg in messages:
                print(msg[0],'posted:',msg[1])
              print()

            self.state = self.states.OFFLINE_SUBSCRIPTIONS
            input("press enter to continue")


    def handle_SUBSCRIPTIONS_MAIN(self):
        #request a list of subscriptions
        msg = self.new_message(message_type = 'subscriptions')
        msg['contents']['message'] = 'get_subscriptions'
        self.send_data(json.dumps(msg))
        
        #wait for response from server
        response = self.get_json()
        subscriptions = response['contents']['message']

        choice = 0
        while choice < 1 or choice > 3:
          os.system('clear')
          print('***************************')
          print('Your Subscriptions')
          print('***************************')
          
          if len(subscriptions) == 0:
            print('You have no subscriptions')
          else:
            for sub in subscriptions:
              print(sub)
          print('***************************')
          print('1 - Add a subscription')
          print('2 - Delete a subscription')
          print('3 - Back to main menu')
          print('***************************')

          choice = input('enter choice: ')
          if choice.isnumeric():
              choice = int(choice)
          else:
              choice = 0

          #if I'm trying to add a subscription
          if choice == 1:
            #self.state = self.states.SUBSCRIPTIONS_ADD
            print()
            print('Who would you like to subscribe to?')

            leader = input('Enter name: ')
            if leader not in subscriptions and leader != self.username:
              #create a subscription where this user is following
              #leader
              #request to insert new subscription 
              msg = self.new_message(message_type = 'subscriptions')
              msg['contents']['message'] = 'new_subscription'
              msg['contents']['leader'] = leader
              self.send_data(json.dumps(msg))
              
              #wait for response from server
              response = self.get_json()

              if response['contents']['message'] == 'ok':
                print('new subscription added')
              else:
                print('failed to add subscription (does this user exist?)')
                choice = 0 #stay in menu loop, don't refresh page

              input('**press enter to continue**')
            
            elif leader == self.username:
              print('You can\'t subscribe to yourself')
              choice = 0 #hacky way to force us back into this while loop
              print() 
              input('**press enter to continue**')

            else:
              print('You are already subscribed to', leader)
              choice = 0 #hacky way to force us back into this while loop
              print() 
              input('**press enter to continue**')

          #I want to delete a subscription
          if choice == 2:
            #self.state = self.states.SUBSCRIPTIONS_DELETE
            print()
            print('Who would you like to unsubscribe to?')
            leader = input('Enter name: ')

            if leader not in subscriptions:
              print('You don\'t have a subscription to',leader)
              choice = 0
              input('**press enter to continue**')
            else:
              #send request to delete a subscription
              msg = self.new_message(message_type = 'subscriptions')
              msg['contents']['message'] = 'delete_subscription'
              msg['contents']['leader'] = leader
              self.send_data(json.dumps(msg))
              
              #wait for response from server
              response = self.get_json()

              if response['contents']['message'] == 'ok':
                print('Your subscription with',leader,'has been deleted')
              else:
                print('failed to delete subscription')
                choice = 0 #stay in menu loop, don't refresh page

              input('**press enter to continue**')

          #go back to the main menu
          if choice == 3:
            self.state = self.states.MAIN_MENU


    def handle_SUBSCRIPTIONS_ADD(self):
      print()
      print('Who would you like to subscribe to?')
      leader = input('Enter name: ')

      input('press enter to go back')
      self.state = self.states.SUBSCRIPTIONS_MAIN


    def handle_SUBSCRIPTIONS_DELETE(self):
      input('press enter to go back')
      self.state = self.states.SUBSCRIPTIONS_MAIN


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


    def print_main_menu(self):
        os.system('clear')
        menu =  '***************************************\n'
        menu += self.username + '\'s Dashboard\n'
        menu += '***************************************\n'
        menu += '1 - See offline messages\n'
        menu += '2 - Edit subscriptions\n'
        menu += '3 - Make a post\n'
        menu += '4 - Hashtag search\n'
        menu += '5 - Logout\n'
        menu += '***************************************'

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


    #the first menu for offline messages
    #where users can choose to see all messages or 
    #just those from a certain subscription
    def print_offline_menu_main(self):
        os.system('clear')
        menu =  '***************************\n'
        menu += 'Offline Messages\n'
        menu += '***************************\n'
        menu += '1 - All subscriptions\n'
        menu += '2 - Select subscription\n'
        menu += '3 - Back to Main Menu\n'
        menu += '****************************'

        choice = 0
        while choice < 1 or choice > 3:
            print(menu)
            choice = input('enter choice: ')
            if choice.isnumeric():
                choice = int(choice)
            else:
                return 0
        if self.debug:
            print('choice is valid!')
        return choice

    #menu that is a list of subscriptions, and the return value 
    #0 to len-1 for a list index (subscription), or len, which is
    #go back
    def subscription_menu(self, menu_name, list_of_options):
      choice = None
      while choice == None or choice < 1 or choice > len(list_of_options)+1:
          os.system('clear')
          print('*********************************')
          print(menu_name)
          print('*********************************')
          choices = ''
          for num, option in enumerate(list_of_options):
            choices += str(num+1) + ' - ' + option
            if num < len(list_of_options)-1:
              choices += '\n'
          print(choices)
          print(len(list_of_options)+1,'-','Back to previous menu')
          print('***************************')
          
          choice = input('enter choice: ')
          if choice.isnumeric():
              choice = int(choice)
          else:
              return None 
      if self.debug:
          print('choice is valid!')
      return choice-1


#end of twidder client class 


if __name__ == '__main__':

    twidder_user = TwidderClient()
    twidder_user.run()
