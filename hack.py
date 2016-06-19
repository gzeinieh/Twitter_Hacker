import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, Response, current_app
import tweepy

#########################
#########Twitter#########
#########################


class TwitterAuth():

    def __init__(self, CONSUMER_KEY,CONSUMER_SECRET, ACCESS_KEY, ACCESS_SECRET):
        self.CONSUMER_KEY = CONSUMER_KEY
        self.CONSUMER_SECRET = CONSUMER_SECRET
        self.ACCESS_KEY = ACCESS_KEY
        self.ACCESS_SECRET = ACCESS_SECRET
        self.auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        self.auth.set_access_token(ACCESS_KEY, ACCESS_SECRET)
        self.api = tweepy.API(self.auth)


T = TwitterAuth('xxxx', 'xxxxxxxxx', 'xxxxxxx', 'xxxxxxx')

auth = T.auth

api = T.api


def get_all_tweets_one_user(screen_name):
    """

    :param screen_name:
    :return: csv with all tweets of a specified user

    get_all_tweets_one_user('gianluigibuffon')
    """

    all_tweets = tweepy.Cursor(api.user_timeline, screen_name=screen_name).items()

    out_tweets = [[tweet.id_str, tweet.created_at, tweet.text] for tweet in all_tweets]

    for tweet in out_tweets:
        db = get_db()

        db.execute("INSERT INTO entries VALUES (?,?,?)",
                  (tweet[0], tweet[1], tweet[2]))

        db.commit()

    pass

    return True


######################
#### application ####
######################


app = Flask(__name__)
app.config.from_object(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'tweet.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('TWEET_SETTINGS', silent=True)

def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv

def init_db():
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()

@app.cli.command('initdb')
def initdb_command():
    """Initializes the database."""
    init_db()
    print("Initialized the database.")

def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """

    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db

@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()

@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('select date_time, tweet from entries order by date_time desc')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)



@app.route('/add', methods=['GET','POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)

    init_db()

    get_all_tweets_one_user(request.form['word'])

    flash("These are all the tweets ;)")


    return redirect(url_for('show_entries'))




@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    init_db()
    flash('You were logged out')
    return redirect(url_for('show_entries'))



