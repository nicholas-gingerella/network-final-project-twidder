#!/bin/env/python
#File: twidder_server.py
#Author: Nicholas Gingerella

from twisted.internet import reactor, protocol, endpoints
from twisted.internet.defer import Deferred
from twisted.protocols import basic
from myEnum import enum
import sys
import signal
import json
import threading

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

    self.factory.msg_recv_count += 1
    message_count = self.factory.msg_recv_count

    if self.debug:
      print self.current_state
      print 'message count', self.factory.msg_recv_count
      print 'connected users:'
      for u in self.factory.connected_users:
        print u


    if self.current_state == self.factory.twidder_states.LOGIN:
      self.handle_LOGIN(data)
    elif self.current_state == self.factory.twidder_states.USER:
      self.handle_USER(data)
    else:
      print 'How did you get here?'


  #========================================================
  # State Handling Methods 
  #========================================================
  
  def handle_LOGIN(self, data):
    global user_count

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
    if user in self.factory.user_logins and user_pass == self.factory.user_logins[user]["password"]:
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
    print 'User:' + self.user_id + ' is gonna ask me for stuff.....'

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

    #list of "registered" users
    #can't use twidder server unless these logged in with one of these credentials
    #also contains info about who each user is subscribed to (subscribed_to)
    #and who has subscribed to them (subscribers)
    user_logins = {
        "user1":{"password":'asdf', "subscribed_to":['user3'], "subscribers":['user2']},
        "user2":{"password":'1234', "subscribed_to":['user1', 'user3'], "subscribers":['user1']},
        "user3":{"password":'wasd', "subscribed_to":[], "subscribers":['user2']}
        }
    #user_logins = {"user1":'asdf', "user2":'1234', "user3":'wasd'}

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
    cmd = raw_input("cmd:")
    if cmd == 'messagecount':
      print message_count 
    if cmd == 'usercount':
      print user_count
    

#create thread for getting input
input_thread = threading.Thread(target=input_thread)
input_thread.daemon = True
input_thread.start()

#create server and start listening on port 8000
endpoints.serverFromString(reactor, 'tcp:8000').listen(TwidderFactory())
#start the reactor!
reactor.run()


