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
            pid INTEGER PRIMARY KEY AUTOINCREMENT,
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
            tid INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL
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
            tag_id INTEGER,
            post_id INTEGER, 
            PRIMARY KEY(tag_id, post_id),
            FOREIGN KEY(tag_id) REFERENCES hashtags(tid),
            FOREIGN KEY(post_id) REFERENCES posts(pid)
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
                          (7, 9),
                          (2, 9)
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
                          ('nick','enrique',2),
                          ('enrique','carla',0),
                          ('dustin','tom', 1),
                          ('tom','enrique',0),
                          ('carla','dustin', 2),
                          ('dustin','carla',0)
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
            SELECT follower_id 
            FROM subscribes
            WHERE leader_id="'''+leader+'''"
        '''
        result = self.exec_query(sql)
        return result


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


    #get all posts or a certain users posts
    def get_posts(self, user=None):
        sql = ''
        if user != None:
            sql = 'SELECT * FROM posts WHERE uid="'+user+'" ORDER BY pid DESC'
        else:
            sql = 'SELECT * FROM posts ORDER BY pid DESC'
        return self.exec_query(sql)


    #get all posts who have a certain hashtag
    #returned posts are ordered from most recent to oldest
    def get_posts_by_tag(self, tag):
        search_tag = tag.lower()
        sql = '''
            SELECT posts.pid, posts.uid, posts.content 
            FROM posts
            INNER JOIN describes ON describes.post_id=posts.pid
            INNER JOIN hashtags ON hashtags.tid=describes.tag_id
            WHERE
            hashtags.content="'''+search_tag+'''"
            ORDER BY pid DESC
        '''
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

    print 'All Posts'
    result = mydb.get_posts()
    for row in result:
        print row
    print ''

    print 'All Subscriptions'
    result = mydb.get_subscriptions()
    for row in result:
        print row
    print ''

    print 'Nick\'s unread subscriptions'
    result = mydb.get_unread_subscriptions('nick')
    for row in result:
        print row
    print ''

    print 'Tom\'s unread subscriptions'
    result = mydb.get_unread_subscriptions('tom')
    for row in result:
        print row
    print ''

    print 'Dustin\'s unread subscriptions'
    result = mydb.get_unread_subscriptions('dustin')
    for row in result:
        print row
    print ''

    print 'Unread Messages from Nick\'s subscription with Tom'
    result = mydb.get_unread_messages('nick','tom')
    for row in result:
        print row
    print ''

    print 'Unread Messages from Carla\'s subscription with Dustin'
    result = mydb.get_unread_messages('carla','dustin')
    for row in result:
        print row
    print ''

    print 'Unread Messages from Enrique\'s subscription with Carla'
    result = mydb.get_unread_messages('enrique','carla')
    for row in result:
        print row
    print ''

    print 'Unread Messages from Dustin\'s subscription with Tom'
    result = mydb.get_unread_messages('dustin','tom')
    for row in result:
        print row
    print ''

    print 'Messages that have the hashtag "#bmw"'
    result = mydb.get_posts_by_tag('#bmw')
    for row in result:
        print row
    print ''

    print 'Nick\'s followers"'
    result = mydb.get_followers('nick')
    for row in result:
        print row
    print ''

    print 'Enrique\'s followers"'
    result = mydb.get_followers('enrique')
    for row in result:
        print row
    print ''

    print 'authorize user test'
    mydb.authorize_user('dustin','wasd')

    print 'all unread messages for nick'
    result = mydb.get_all_unread_messages('nick')

    mydb.print_table('subscribes') 

    print 'clear unread messages for nicks susbcription with tom'
    mydb.clear_unread('nick','tom')

    mydb.print_table('subscribes') 

    print 'increment unread for nicks subscription with tom'
    mydb.increment_unread('nick','tom')


    mydb.print_table('subscribes') 
    print 'inserting some subscriptions'
    mydb.insert_subscription('carla','tom')
    mydb.insert_subscription('carla','carla')
    mydb.insert_subscription('ballsdeep69','carla')
    mydb.insert_subscription('enrique','tom')
    mydb.print_table('subscribes') 
