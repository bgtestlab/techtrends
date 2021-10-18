import sqlite3
import logging.config
import json
import requests

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash

db_connection_count = 0

# Create logger
with open('logger.json', 'r') as f:
    config = json.load(f)
logger = logging.getLogger('app')
logging.config.dictConfig(config)


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    global db_connection_count
    db_connection_count += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()

    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'


@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute('SELECT count(*) FROM posts').fetchone()[0]
    connection.close()

    response = app.response_class(
        response=json.dumps({"db_connection_count": db_connection_count, "post_count": post_count}),
        status=200,
        mimetype='application/json'
    )

    logger.info('Metrics request successful!')
    return response


# Health check depending on status code
@app.route('/healthz')
def healthcheck():
    res = {
        'response': {},
        'status': 0
    }

    req = requests.get('http://127.0.0.1:3111/')
    res['status'] = req.status_code
    if res['status'] == 200:
        result = 'OK - healthy'
        logger.info('Status request successful!')
    else:
        result = 'Not OK - unhealthy'
        logger.info('Status request unsuccessful!')
    res['response'] = {'result': result}

    response = app.response_class(
        response=json.dumps(res['response']),
        status=res['status'],
        mimetype='application/json'
    )

    return response


# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logger.error('Non-existing article is accessed!')
        return render_template('404.html'), 404
    else:
        logger.debug('Article ' + '\"' + post[2] + '\"' + ' retrieved!')
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    logger.debug('About Us is accessed!')
    return render_template('about.html')


# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            return redirect(url_for('index'))

    logger.debug('A new article is created!')
    return render_template('create.html')


# start the application on port 3111
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='3111', debug=True)
