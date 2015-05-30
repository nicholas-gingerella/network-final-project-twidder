#!/bin/env/python
#File: twidder_server.py
#Author: Nicholas Gingerella

from twisted.internet import reactor, protocol, endpoints
from twisted.internet.defer import Deferred
from twisted.protocols import basic
from myEnum import enum
from twidder_db import TwidderDB
import sys
import signal
import json
import threading

#globals that are used for
DB = TwidderDB()
message_count = 0
user_count = 0

class TwidderProtocol(protocol.Protocol):
  current_state = None
  user_id = ''
  debug = False

  #pass flag to script to output debug messages
  if len(sys.argv) > 1:
    if sys.argv[1] == 'd':
      debug = True


  def connectionMade(self):
    if self.debug:
      print 'client has connected'
    self.current_state = self.factory.twidder_states.LOGIN


  #when a client closes the connection, or the connection is lost,
  #this runs
  def connectionLost(self, reason):
      global user_count

      if self.debug:
        print 'lost connection to client'

      #since the user is logging off, delete them from
      #the list of currently connected users
      if self.user_id in self.factory.connected_users:
        if self.debug:
          print 'deleting current user'
          print self.factory.connected_users

        #delete this user from the list of connected users
        del self.factory.connected_users[self.user_id]

        if self.debug:
          print 'after deletion'
          print self.factory.connected_users

        #update the connected user count, for both the factory
        #AND the global user_count variable (used by input thread)
        self.factory.connected_user_count = len(self.factory.connected_users)
        user_count = self.factory.connected_user_count


  #Whenever the server recieves data from any of the clients, this method
  #will run
  def dataReceived(self, data):
    global message_count

    #increment number of messages that server has received
    self.factory.msg_recv_count += 1
    message_count = self.factory.msg_recv_count

    if self.debug:
      print self.current_state
      print 'message count', self.factory.msg_recv_count
      print 'connected users:'
      for u in self.factory.connected_users:
        print u

    #state transitions
    if self.current_state == self.factory.twidder_states.LOGIN:
      self.handle_LOGIN(data)
    elif self.current_state == self.factory.twidder_states.USER:
      self.handle_USER(data)
    else:
      print 'How did you get here?'


  #check if data can be converted into a json object
  #if so, return the object, else return None
  def makeJSON(self,data):
    msg = None
    try:
      msg = json.loads(data)
      return msg
    except:
      print 'ERROR: not a proper JSON message'
      return None



  #========================================================
  # State Handling Methods 
  #========================================================
  
  def handle_LOGIN(self, data):
    global user_count, DB

    json_msg = None
    try:
      json_msg = json.loads(data)
    except:
      print 'ERROR: not a proper JSON message'
      fail_msg = self.newMessage(message_type ='login') 
      fail_msg["contents"]["message"] = 'fail'
      self.transport.write(json.dumps(fail_msg))
      return

    #the request is not a login request, send an error message
    if not self.isUserLoginRequest(json_msg):
      if self.debug:
        print 'Not a login request'
        fail_msg = self.newMessage(message_type ='error') 
        fail_msg["contents"]["message"] = 'error'
        self.transport.write(json.dumps(fail_msg))
        return


    #get the username and password from the received message
    user = json_msg["contents"]["message"]["username"]
    user_pass = json_msg["contents"]["message"]["password"]

    #if a valid username and password are received, let this user enter the USER state
    if DB.authorize_user(user, user_pass): 
      #assign user name of this connection
      self.user_id = user

      #add user to connected users
      self.factory.connected_users[user] = self

      #update current user count
      self.factory.connected_user_count = len(self.factory.connected_users)
      user_count = self.factory.connected_user_count

      #switch the user to the USER state
      self.current_state = self.factory.twidder_states.USER

      #build a success message and send it to user
      success_msg = self.newMessage(message_type = 'login')
      success_msg["contents"]["message"] = 'ok'
      self.transport.write(json.dumps(success_msg))

      if self.debug:
        print 'user ' + self.user_id + ' authenticated'
        print 'connected users:'
        for u in self.factory.connected_users:
          print u

      return
    else:
      if self.debug:
        print 'bad credentials'

    #if you got here, 
    #construct a failure message to send to client
    fail_msg = self.newMessage(message_type ='login') 
    fail_msg['contents']['message'] = 'fail'
    self.transport.write(json.dumps(fail_msg))



  def handle_USER(self, data):
    global DB

    json_msg = self.makeJSON(data)
    if json_msg == None:
      if self.debug:
        print 'ERROR: not a proper JSON message'
        fail_msg = self.newMessage(message_type = 'response')
        fail_msg['contents']['message'] = 'fail'
        self.transport.write(json.dumps(fail_msg))

    #******************************************************
    # Unread Message Handling
    #******************************************************
    #if the client sent us a request for offline messages
    #******************************************************
    if json_msg['message_type'] == 'request':
        if self.debug:
            print 'request from', self.user_id, 'received'

        if json_msg['contents']['message'] == 'all_unread':
            #get all unread messages for this user from the database
            unreadMessages = DB.get_all_unread_messages(self.user_id)

            #send the messages back to the user
            response = self.newMessage( message_type = 'response' )
            response['contents']['message'] = unreadMessages
            self.transport.write(json.dumps(response))

        elif json_msg['contents']['message'] == 'get_subscriptions':
            #I need to get the subscriptions, and send them back to the
            #user, this way, the user can send me which subscription he
            #wants to get messages from
            result = DB.get_subscriptions(self.user_id)

            #extract the names from the tuples in the result, to make life
            #easier for the client side
            user_subscriptions = []
            for row in result:
                user_subscriptions.append(row[0])
            
            #now we simply have a list of user ids who the current user is subscribed to
            #send the subscriptions back to the user
            response = self.newMessage( message_type = 'response' )
            response['contents']['message'] = user_subscriptions 
            self.transport.write(json.dumps(response))

        elif json_msg['contents']['message'] == 'unread':
            leader = json_msg['contents']['leader']

            #get unread messages from a certain subscription 
            leader = json_msg['contents']['message']
            unreadMessages = DB.get_unread_messages(self.user_id, leader)

            #send the messages back to the user
            response = self.newMessage( message_type = 'response' )
            response['contents']['message'] = unreadMessages
            self.transport.write(json.dumps(response))
        else:
            #send the messages back to the user
            response = self.newMessage( message_type = 'response' )
            response['contents']['message'] = 'fail' 
            self.transport.write(json.dumps(response))

    if self.debug:
        print 'in user state'

  #========================================================
  #  End State Handling Methods 
  #========================================================

  def isUserRequest(self, json_msg):
    fields = ('sender', 'message_type', 'contents')
    if all (field in json_msg for field in fields):
      if json_msg['sender'] in self.factory.connected_users:
        return True
    return False


  def isUserLoginRequest(self, json_msg):
    fields = ('sender', 'message_type', 'contents')
    if all (field in json_msg for field in fields):
      if self.debug:
        print 'all login request fields are present'
      if json_msg['message_type'] == 'login':
        if self.debug:
          print 'message type is a login'
        if 'username' in json_msg['contents']['message'] and 'password' in json_msg['contents']['message']:
          if self.debug:
            print 'message contains username and pass'
          return True
    return False


  #creates a dictionary with basic formatting for messages
  def newMessage(self, message_type, sender='twidder'):
    new_msg = {}
    new_msg["sender"] = sender
    new_msg["message_type"] = message_type
    new_msg["contents"] = {"message":''}
    return new_msg



#stores info common to all connections
class TwidderFactory(protocol.ServerFactory):
    protocol = TwidderProtocol
    
    #enumerations as state variables
    twidder_states = enum('LOGIN', 'USER')

    #if a user is not logged in when a message arrives, it is stored in the offline messages
    #dictionary. When they log on and request the offline messages, they will all be sent to
    #the user
    offline_messages = {"user1":[]}
    user_subscriptions = {"user1":['user3'], "user2":['user1','user3'], "user3":[]}

    connected_user_count = 0
    msg_recv_count = 0

    #dict of currently connected users
    #key = userid
    #val = transport object for communication
    connected_users = {}


#thread for getting input from server admin while the
#reactor framework runs
def input_thread():
  while True:
    cmd = raw_input("admin ~> ")
    if cmd == 'messagecount':
      print 'Messages received:',message_count 
    if cmd == 'usercount':
      print 'Logged in users:',user_count
    

#create thread for getting input
input_thread = threading.Thread(target=input_thread)
input_thread.daemon = True
input_thread.start()

#create server and start listening on port 8000
endpoints.serverFromString(reactor, 'tcp:8000').listen(TwidderFactory())
#start the reactor!
reactor.run()


