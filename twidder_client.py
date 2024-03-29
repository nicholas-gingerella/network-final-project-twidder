#!/bin/env/python
import socket
from base64 import *
import os
import errno
import sys
import signal
import time
import threading
import json
from getpass import getpass
from twidder_utilities import *

#signal handler for ctrl-c (SIGINT)
def sigint_handler(signal, fram):
    print('\nClosing client...\n')
    sys.exit(0)
signal.signal(signal.SIGINT,sigint_handler)

class TwidderClient:

    def __init__(self, targetHost = '127.0.0.1', portNum = 8000):
        self.username = ''
        self.password = ''
        self.num_unread_messages_seen = False
        self.num_unread_messages = 0
        self.states = enum('LOGIN','CONNECT','MAIN_MENU',
                           'OFFLINE_MAIN', 'OFFLINE_ALL', 'OFFLINE_SUBSCRIPTIONS',
                           'SUBSCRIPTIONS_MAIN','SUBSCRIPTIONS_ADD','SUBSCRIPTIONS_DELETE',
                           'FOLLOWERS_MAIN',
                           'NEW_POST',
                           'HASHTAG_SEARCH',
                           'LOGOUT'
                           )
        self.state = self.states.LOGIN
        self.sock = None
        self.msg_sock = None
        self.msg_thread = None
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


    def get_msg_socket(self):
        # try to create a socket, if creation of socket fails, then simply
        # kill the client
        try:
            self.msg_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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


    #connect a differnt socket for receiving messages from other posters
    def msg_connect(self):
        self.get_msg_socket()
        try:
            self.msg_sock.connect((self.host,self.port)) #connect to same server, but from different socket
        except:
            print('msg connection refused')
            sys.exit()


    def disconnect(self):
        self.sock.close()
        if self.msg_sock != None:
            self.msg_sock.close()


    def send_data(self, data):
        try:
            self.sock.sendall(data.encode())
        except OSError as e:
            print('ERROR:',e)


    def send_msg_data(self, data):
        try:
            self.msg_sock.sendall(data.encode())
        except OSError as e:
            print('ERROR:',e)


    def get_data(self):
        try:
            data = self.sock.recv(4096)
        except OSError as e:
            print("ERROR:",e)
        data = data.decode()
        return data

    def get_msg_data(self):
        try:
            data = self.msg_sock.recv(4096)
        except OSError as e:
            pass
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



    def get_msg_json(self):
        data = None

        try:
            data = self.msg_sock.recv(4096)
        except OSError as e:
            return False

        if self.debug:
            print('data before decode:',data)

        if data == None:
            return False

        data = data.decode()
        if self.debug:
            print('data after decode:')
            print(json.dumps(data,indent=4))
        try:
            json_data = json.loads(data)
        except:
            return
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

            elif self.state == self.states.FOLLOWERS_MAIN:
                self.handle_FOLLOWERS_MAIN()

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
        encoded_password = b64encode(self.password.encode('ascii')).decode()
        msg = self.new_message(message_type = 'login')
        msg['contents']['message'] = {  "username":self.username,
                                        "password":encoded_password}

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

                    #now try to create another connection, but this one will
                    #be for a different socket, one meant only to receive live messages
                    self.msg_connect()

                    #create a login message for the live feed for this user
                    msg = self.new_message(message_type = 'login_live')
                    msg['contents']['message'] = {  "username":self.username,
                                                    "password":self.password}
                    self.send_msg_data(json.dumps(msg))

                    #wait for response from server
                    #or wait for timeout
                    response = self.get_msg_json()
                    if response['contents']['message'] == 'ok':
                        #create thread, do something
                        self.msg_thread = threading.Thread(target=self.live_feed)
                        self.msg_thread.daemon = True
                        self.msg_thread.start()
                    else:
                        print('live feed connect failed')
                        input('press enter')
                        
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
        if self.num_unread_messages_seen == False:
            #request number of unread messages
            msg = self.new_message(message_type = 'offline_messages')
            msg['contents']['message'] = 'get_num_unread'
            self.send_data(json.dumps(msg))
            
            #wait for response
            response = self.get_json()
            self.num_unread_messages = response['contents']['message']
            self.num_unread_messages_seen = True


        choice = self.print_main_menu()
        
        #based on input, decide which state to go to
        if choice == 1:
            self.state = self.states.OFFLINE_MAIN
        elif choice == 2:
            self.state = self.states.SUBSCRIPTIONS_MAIN
        elif choice == 3:
            self.state = self.states.FOLLOWERS_MAIN
        elif choice == 4:
            self.state = self.states.NEW_POST
        elif choice == 5:
            self.state = self.states.HASHTAG_SEARCH
        elif choice == 6:
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
        self.num_unread_messages = 0
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
              print('-',sub)
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


    def handle_FOLLOWERS_MAIN(self):
        #request a list of followers 
        msg = self.new_message(message_type = 'followers')
        msg['contents']['message'] = 'get_followers'
        self.send_data(json.dumps(msg))
        
        #wait for response from server
        response = self.get_json()

        followers = response['contents']['message']
        print('followers')
        
        os.system('clear')
        print('***************************')
        print('Your Followers')
        print('***************************')
        if len(followers) == 0:
            print('You have no followers')
        else:
            for fan in followers:
                print('-',fan)
        print('***************************\n')
        input('**press enter to continue**')
        self.state = self.states.MAIN_MENU


    def handle_POST(self):
        #request a list of 5 most recent posts
        msg = self.new_message(message_type = 'posts')
        msg['contents']['message'] = 'get_posts'
        self.send_data(json.dumps(msg))
        
        #wait for response from server
        response = self.get_json()
        posts = response['contents']['message']

        choice = 0
        while choice < 1 or choice > 3:
            os.system('clear')
            print('**********************************************')
            print('Posts')
            print('**********************************************')
            if len(posts) == 0:
                print('You have no posts')
            else:
                for p in posts:
                    print('-',p)
            print('**********************************************')
            print('1 - Make a new post')
            print('2 - Back to main menu')
            print('**********************************************')
            choice = input('enter choice: ')
            if choice.isnumeric():
                choice = int(choice)
            else:
                choice = 0
            
            if choice == 1:
                print()
                new_post = input('Enter post: ')
                if new_post == '':
                    choice = 0
                    continue
                else:
                    if len(new_post) > 140:
                        print('Your post cannot exceed 140 characters')
                        input('**press enter to continue**')
                        choice = 0
                        continue
                        
                print()
                print('Enter hashtags for this post, seperated by spaces')
                print('Example: #tag1 #tag2 #tag3 #tag4')
                post_tags = input('Hashtags: ')

                tag_list = post_tags.split()

                #send a request to create the post
                msg = self.new_message(message_type = 'posts')
                msg['contents']['message'] = 'create_post'
                msg['contents']['post'] = new_post
                msg['contents']['tags'] = tag_list
                self.send_data(json.dumps(msg))
                
                #wait for response from server
                response = self.get_json()

                if response['contents']['message'] == 'ok':
                    print('Post created')
                    input('**press enter to continue**')
                else:
                    print('Failed to create post')
                    choice = 0 #stay in menu loop, don't refresh page

            elif choice == 2:
                self.state = self.states.MAIN_MENU


    def handle_SEARCH(self):
        while True:
            os.system('clear')
            print('***************************')
            print('Hashtag Search')
            print('***************************')
            tag = input('Enter a hashtag (enter nothing to go back)\n')
            print()

            tag.replace(' ','')#get rid of spaces
            
            if tag != '':
                if not tag.startswith('#'):
                    tag = '#' + tag

                #send request for posts by hashtag
                msg = self.new_message(message_type = 'hashtags')
                msg['contents']['message'] = 'get_posts'
                msg['contents']['tag'] = tag 
                self.send_data(json.dumps(msg))
                
                #wait for response from server
                response = self.get_json()

                posts = response['contents']['message']
                
                #if there are posts display them, if not, say so
                if len(posts) < 1:
                    print('-------------------------------')
                    print('No posts with this hashtag')
                    print('-------------------------------')
                    print()
                else:
                    print('-------------------------------')
                    print('Posts with hashtag',tag)
                    print('-------------------------------')
                    for post in posts:
                        print('- [{n}]: {p}'.format(n=post[1],p=post[0]))
                    print('-------------------------------')
                    print()

                input('**press enter to continue**')
            else:
                self.state = self.states.MAIN_MENU
                break




    def handle_LOGOUT(self):
        #if we got here, then the credentials werent correct, go back to 
        #login screen
        self.num_unread_messages_seen = False 
        self.num_unread_messages = 0
        self.disconnect()
        self.state = self.states.LOGIN

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
        if self.num_unread_messages > 0:
            menu += 'You have ' + str(self.num_unread_messages) + ' messages\n'
        menu += '***************************************\n'
        menu += '1 - See offline messages\n'
        menu += '2 - Edit subscriptions\n'
        menu += '3 - View followers\n'
        menu += '4 - Make a post\n'
        menu += '5 - Hashtag search\n'
        menu += '6 - Logout\n'
        menu += '***************************************'

        choice = 0
        while choice < 1 or choice > 6:
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


    def live_feed(self):
        sender = ''
        post = ''
        while True:
            response = self.get_msg_json()
            if response == False or response == None:
                return
            sender = response['contents']['message']['sender']
            post = response['contents']['message']['post']
            print('\n--------------------------------------------------------------')
            print('[{name}] posted: {msg}'.format(name=sender,msg=post))
            print('--------------------------------------------------------------')
                

#end of twidder client class 


if __name__ == '__main__':

    twidder_user = TwidderClient()
    twidder_user.run()
