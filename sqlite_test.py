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
                     (1,'nick','Vegetables are like Cryptonite to me D:>'),
                     (2,'tom','When nick has a heart attack, I will lol so hard!'),
                     (3,'dustin','doors...how do they work?'),
                     (4,'dustin','I really like the Macs that have the graphics card!'),
                     (5,'dustin','I luv Ham! :)'),
                     (6,'dustin','Die in a fire...with all due respect :)'),
                     (7,'carla','Henk Henk'),
                     (8,'enrique','Crickets are pretty tasty, especially the brown ones!'),
                     (9,'enrique','woke up late for school again, just gonna skip it!'),
                     (10,'enrique','por que no los dos?')
                    ]
        self.db_cursor.executemany('INSERT INTO posts VALUES (?,?,?)',new_posts)

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
        new_subscribes = [('nick','tom', 1),
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


    def insert_user(self, user, passw):
        u = (user,passw)
        self.db_cursor.execute('INSERT INTO users VALUES (?,?)', u)
        self.db_connection.commit()


    #the toughest query so far, getting the most recent unread posts from one of the subscribers you are currently
    #subscribed to.
    def get_unread_messages(self, follower, leader):
        num_unread = self.exec_query('SELECT unread FROM subscribes WHERE follower_id="'+follower+'" and leader_id="'+leader+'"')
        if len(num_unread[0]) < 1:
            return []

        num_unread = num_unread[0][0]
        sql = '''
            SELECT pid, uid, content
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


    #get all posts or a certain users posts
    def get_posts(self, user=None):
        sql = ''
        if user != None:
            sql = 'SELECT * FROM posts WHERE uid="'+user+'" ORDER BY pid DESC'
        else:
            sql = 'SELECT * FROM posts ORDER BY pid DESC'
        return mydb.exec_query(sql)


    #get all subscriptions or subscriptions for a certain user
    def get_subscriptions(self, user=None):
        sql = ''
        if user != None:
            sql = 'SELECT * FROM subscribes WHERE follower_id="'+user+'"'
        else:
            sql = 'SELECT * FROM subscribes'
        return mydb.exec_query(sql)


    def print_table(self, table):
        self.db_cursor.execute('SELECT * FROM ' + table)
        rows = self.db_cursor.fetchall()
        for row in rows:
            print(row)

# END TwidderDB class



if __name__ == '__main__':
    mydb = TwidderDB()
    print("users table")
    print("+++++++++++++++++++++++")
    mydb.print_table('users')
    print("+++++++++++++++++++++++")
    print()

    print("posts table")
    print("+++++++++++++++++++++++")
    mydb.print_table('posts')
    print("+++++++++++++++++++++++")
    print()

    print("subscribes table")
    print("+++++++++++++++++++++++")
    mydb.print_table('subscribes')
    print("+++++++++++++++++++++++")
    print()

    print('All Posts')
    result = mydb.get_posts()
    for row in result:
        print(row)
    print()

    print('All Subscriptions')
    result = mydb.get_subscriptions()
    for row in result:
        print(row)
    print()

    print('Nick\'s unread subscriptions')
    result = mydb.get_unread_subscriptions('nick')
    for row in result:
        print(row)
    print()

    print('Tom\'s unread subscriptions')
    result = mydb.get_unread_subscriptions('tom')
    for row in result:
        print(row)
    print()

    print('Dustin\'s unread subscriptions')
    result = mydb.get_unread_subscriptions('dustin')
    for row in result:
        print(row)
    print()

    print('Unread Messages from Nick\'s subscription with Tom')
    result = mydb.get_unread_messages('nick','tom')
    for row in result:
        print(row)
    print()

    print('Unread Messages from Carla\'s subscription with Dustin')
    result = mydb.get_unread_messages('carla','dustin')
    for row in result:
        print(row)
    print()

    print('Unread Messages from Enrique\'s subscription with Carla')
    result = mydb.get_unread_messages('enrique','carla')
    for row in result:
        print(row)
    print()

    print('Unread Messages from Dustin\'s subscription with Tom')
    result = mydb.get_unread_messages('dustin','tom')
    for row in result:
        print(row)
    print()
