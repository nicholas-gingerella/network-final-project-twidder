#author: Nicholas Gingerella
#cs164 - Networks
import sqlite3


class TwidderDB(object):

    def __init__(self, db = ':memory:'):
        self.db_name = db
        self.db_connection = sqlite3.connect(self.db_name) 
        self.db_cursor = self.db_connection.cursor()

        #enable foreign keys
        self.db_cursor.execute('PRAGMA foreign_keys = ON')

        #create tables for database
        user_table = '''
        CREATE TABLE users(
            uid TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
        '''
        self.db_cursor.execute(user_table)
        new_users = [('nick','asdf'),
                     ('tom','1234'),
                     ('dustin','wasd'),
                     ('carla','qwerty'),
                     ('enrique','password')
                    ]
        self.db_cursor.executemany('INSERT INTO users VALUES (?,?)', new_users)

        posts_table = '''
        CREATE TABLE posts (
            pid INTEGER PRIMARY KEY,
            uid TEXT NOT NULL, 
            content TEXT NOT NULL,
            FOREIGN KEY(uid) REFERENCES users(uid)
        )
        '''
        self.db_cursor.execute(posts_table)
        new_posts = [(0,'nick','I loves da Twidderz!'),
                     (1,'nick','What does BMW stand for? If I had to take a guess I\'d say Big Meaty Women.'),
                     (2,'tom','When nick has a heart attack, I will lol so hard!'),
                     (3,'dustin','doors...how do they work?'),
                     (4,'dustin','I really like the Macs that have the graphics card!'),
                     (5,'dustin','I luv Ham! :)'),
                     (6,'dustin','Die in a fire...with all due respect :)'),
                     (7,'carla','Henk Henk'),
                     (8,'tom','Beer will solve all of our problems!'),
                     (9,'enrique','Crickets are pretty tasty, especially the brown ones!'),
                     (10,'enrique','GERMAN ENGINEERING!'),
                     (11,'enrique','porkay no lost toast?'),
                     (12,'tom','....unless you get a DUI')
                    ]
        self.db_cursor.executemany('INSERT INTO posts VALUES (?,?,?)',new_posts)

        hashtags_table = '''
        CREATE TABLE hashtags (
            tid INTEGER NOT NULL PRIMARY KEY,
            content TEXT NOT NULL UNIQUE
        )
        '''
        self.db_cursor.execute(hashtags_table)
        new_hashtags = [(0,'#justpsychoticthings'),
                        (1,'#yoloswag420'),
                        (2,'#bmw'),
                        (3,'#howdoesitwork'),
                        (4,'#geese'),
                        (5,'#ham'),
                        (6,'#germans'),
                        (7,'#engineering'),
                       ]
        self.db_cursor.executemany('INSERT INTO hashtags VALUES (?,?)',new_hashtags)

        describes_table = '''
        CREATE TABLE describes (
            tag_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL, 
            FOREIGN KEY(post_id) REFERENCES posts(pid),
            FOREIGN KEY(tag_id) REFERENCES hashtags(tid),
            PRIMARY KEY(tag_id, post_id)
        )
        '''
        self.db_cursor.execute(describes_table)
        new_describes = [ (0, 1),
                          (3, 2),
                          (4, 0),
                          (2, 1),
                          (5, 3),
                          (4, 2),
                          (6, 9),
                          (2, 10)
                        ]
        self.db_cursor.executemany('INSERT INTO describes VALUES (?,?)',new_describes)

        subscribes_table = '''
        CREATE TABLE subscribes (
            follower_id TEXT,
            leader_id TEXT, 
            unread INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(follower_id, leader_id),
            FOREIGN KEY(follower_id) REFERENCES users(uid),
            FOREIGN KEY(leader_id) REFERENCES users(uid)
        )
        '''
        self.db_cursor.execute(subscribes_table)
        new_subscribes = [('nick','tom', 2),
                          ('nick','enrique', 1),
                          ('enrique','carla',0),
                          ('dustin','tom', 1),
                          ('tom','enrique', 2),
                          ('carla','dustin', 2),
                          ('dustin','carla', 1)
                        ]
        self.db_cursor.executemany('INSERT INTO subscribes VALUES (?,?,?)',new_subscribes)
        self.db_connection.commit()


    #execute a general sql query
    def exec_query(self, sql):
        self.db_cursor.execute(sql)
        self.db_connection.commit()
        return self.db_cursor.fetchall()


    #check if this users is found in the database,
    #if so, then this is a registered user and they passed in
    #the correct username and password
    def authorize_user(self,u,p):
        u = u.lower()
        sql = '''
            SELECT uid, password
            FROM users
            WHERE uid="''' + u + '''" AND password="''' + p + '''"
        '''
        result = self.exec_query(sql)
        if len(result) > 0:
            return True
        else:
            return False


    def insert_subscription(self, user, leader):
        s = (user, leader, 0)
        sql = 'INSERT INTO subscribes VALUES (?,?,?)'
        try:
            self.db_cursor.execute(sql,s)
        except sqlite3.Error as e:
            return None

        self.db_connection.commit()
        return True 


    def delete_subscription(self, user, leader):
        sql = 'DELETE FROM subscribes WHERE follower_id="'+user+'" and leader_id="'+leader+'"'
        try:
            self.db_cursor.execute(sql)
        except sqlite3.Error as e:
            return None

        self.db_connection.commit()
        return True 


    def insert_user(self, user, passw):
        u = (user,passw)
        try:
            self.db_cursor.execute('INSERT INTO users VALUES (?,?)', u)
        except sqlite3.Error as e:
            return None

        self.db_connection.commit()
        return True 


    #get the users who are following (subscribed to) leader
    def get_followers(self, leader):
        sql = '''
            SELECT DISTINCT follower_id 
            FROM subscribes
            WHERE leader_id="'''+leader+'''"
        '''
        result = self.exec_query(sql)
        
        clean_result = []
        for row in result:
          clean_result.append(row[0])

        return clean_result 


    #the toughest query so far, getting the most recent unread posts from one of the subscribers you are currently
    #subscribed to.
    def get_unread_messages(self, follower, leader):
        num_unread = self.exec_query('SELECT unread FROM subscribes WHERE follower_id="'+follower+'" and leader_id="'+leader+'"')
        if len(num_unread[0]) < 1:
            return []

        num_unread = num_unread[0][0]
        sql = '''
            SELECT uid, content
            FROM posts INNER JOIN subscribes ON
            posts.uid=subscribes.leader_id
            WHERE subscribes.follower_id="'''+follower+'''" and subscribes.leader_id="'''+leader+ '''"
            ORDER BY pid DESC LIMIT '''+str(num_unread)+'''
        '''
        result = self.exec_query(sql)
        return list(reversed(result))


    #get subscriptions where there are unread messages
    def get_unread_subscriptions(self,user):
        sql = 'SELECT leader_id FROM subscribes WHERE follower_id="'+user+'" and unread > 0 ORDER BY leader_id'
        result = self.exec_query(sql)
        return result


    def get_all_unread_messages(self, user):
        result = self.get_unread_subscriptions(user)
        subscriptions = []
        for row in result:
          subscriptions.append(row[0])
        
        #if there are no subscriptions, don't bother with the rest
        if len(subscriptions) <= 0:
          return None

        #message will be a list of lists
        #where each element is a list of posts by a certain leader
        messages = []
        for leader in subscriptions:
          result = self.get_unread_messages(user, leader)
          messages.append(result)

        return messages 


    #increment the number of unread messages for particular subscription
    def increment_unread(self, user, leader):
        sql = '''
            UPDATE subscribes
            SET unread = unread + 1
            WHERE follower_id="'''+user+'''" and leader_id="'''+leader+'''" 
        '''
        self.exec_query(sql)


    #set unread count to 0 for all subscriptions where user is the follower
    def clear_all_unread(self, user):
        sql = '''
            UPDATE subscribes
            SET unread = 0
            WHERE follower_id = "'''+user+'''" 
        '''
        self.exec_query(sql)


    #set unread count to 0 for particular subscription, where user is the follower
    #and leader is the leader_id of the subscription
    def clear_unread(self, user, leader):
        sql = '''
            UPDATE subscribes
            SET unread = 0
            WHERE follower_id="'''+user+'''" and leader_id="'''+leader+'''" 
        '''
        self.exec_query(sql)


    def create_post(self,user,content,hashtags):
      #use cursor.lastrowid for getting the id of the post that these
      #hashtags are to be associated with

      tags = []
      for tag in hashtags:
        if not tag.startswith('#'):
          #prepend # to tag
          tag = '#' + tag
        tags.append(tag)

      #first insert the  new post into the database
      p = (user,content)
      sql = '''
        INSERT INTO posts (uid,content) VALUES (?,?)
      '''
      try:
        self.db_cursor.execute(sql,p)
      except sqlite3.Error as e:
        #print 'POST INSERT ERROR:',e
        return None 

      #get id of post we just made
      post_id = self.db_cursor.lastrowid

      #now go through list of hashtags, and insert them into
      #the database (but only do all this if we have hashtags)
      if len(tags) > 0:
        for tag in tags:
          t = (tag,)
          sql = '''
            INSERT INTO hashtags (content) VALUES (?)
          '''
          try:
            self.db_cursor.execute(sql,t)
          except sqlite3.Error as e:
            #print 'HASHTAG INSERT ERROR:',e
            pass

        #the hashtags are now in the database
        #now associate all of the hashtag ids
        #with the post id via the describes table
        for tag in tags:
          tid = self.get_hashtag_id(tag)[0][0]
          d = (tid, post_id)
          sql = '''
            INSERT INTO describes (tag_id,post_id) VALUES (?,?)
          '''
          try:
            self.db_cursor.execute(sql,d)
          except sqlite3.Error as e:
            #print 'DESCRIBES INSERT ERROR:',e
            pass

      return True
          


    def get_hashtag_id(self,tag):
      sql = '''
        SELECT tid
        FROM hashtags
        WHERE content="'''+tag+'''"
      '''
      return self.exec_query(sql)


    def get_num_unread(self):
      sql = '''
        SELECT SUM(unread) 
        FROM subscribes 
      '''
      result = self.exec_query(sql)
      if result == None:
        return None
      else:
        return result[0][0]


    #get all posts or a certain users posts
    def get_posts(self, user=None, limit=None):
        sql = ''
        if user != None:
            sql = 'SELECT DISTINCT pid, content FROM posts WHERE uid="'+user+'" ORDER BY pid DESC'
        else:
            sql = 'SELECT DISTINCT pid, content FROM posts ORDER BY pid DESC'

        if limit != None and limit > 0:
            sql += ' LIMIT ' + str(limit)

        return self.exec_query(sql)


    #get all posts who have a certain hashtag
    #returned posts are ordered from most recent to oldest
    def get_posts_by_tag(self, tag, limit=None):
        search_tag = tag.lower()
        sql = '''
            SELECT posts.pid, posts.content 
            FROM posts
            INNER JOIN describes ON describes.post_id=posts.pid
            INNER JOIN hashtags ON hashtags.tid=describes.tag_id
            WHERE
            hashtags.content="'''+search_tag+'''"
            ORDER BY pid DESC'''
        if limit != None:
          sql += ' LIMIT ' + str(limit)

        result = self.exec_query(sql) 
        return result


    #get all subscriptions or subscriptions for a certain user
    def get_subscriptions(self, user=None):
        sql = ''
        if user != None:
            sql = 'SELECT leader_id FROM subscribes WHERE follower_id="'+user+'"'
        else:
            sql = 'SELECT * FROM subscribes'
        return self.exec_query(sql)


    def print_table(self, table):
        self.db_cursor.execute('SELECT * FROM ' + table)
        rows = self.db_cursor.fetchall()
        for row in rows:
            print row

# END TwidderDB class



if __name__ == '__main__':
    mydb = TwidderDB()
    print "users table"
    print "+++++++++++++++++++++++"
    mydb.print_table('users')
    print "+++++++++++++++++++++++\n"

    print "posts table"
    print "+++++++++++++++++++++++"
    mydb.print_table('posts')
    print "+++++++++++++++++++++++\n"

    print "hashtags table"
    print "+++++++++++++++++++++++"
    mydb.print_table('hashtags')
    print "+++++++++++++++++++++++\n"

    print "describes table"
    print "+++++++++++++++++++++++"
    mydb.print_table('describes')
    print "+++++++++++++++++++++++\n"

    print("subscribes table")
    print "+++++++++++++++++++++++"
    mydb.print_table('subscribes')
    print "+++++++++++++++++++++++\n"

    mydb.print_table('subscribes') 

    print 'num unread posts'
    print(mydb.get_num_unread())
