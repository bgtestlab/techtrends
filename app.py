import sqlite3
import logging
import logging.config
import sys
import requests
from flask import (
    Flask,
    abort,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify
)


# Define the Flask application
app = Flask(__name__)
app.config['db_connection_count'] = 0

# Create logger
logger = logging.getLogger('app')
logger.setLevel(logging.DEBUG)

# Set format
format_output = logging.Formatter(
    fmt='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
    datefmt='%Y/%m/%d, %H:%M:%S'
)

# Create console handler and set level to debug
stdout_handler = logging.StreamHandler(sys.stdout)
stderr_handler = logging.StreamHandler(sys.stderr)

stdout_handler.setFormatter(format_output)
stderr_handler.setFormatter(format_output)

# Add handlers
logger.addHandler(stdout_handler)
logger.addHandler(stderr_handler)


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.config['db_connection_count'] += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    post = None
    connection = get_db_connection()
    if connection:
        try:
            post = connection.execute('SELECT * FROM posts WHERE id = ?',
                                      (post_id,)).fetchone()
        except BaseException:
            logger.error('Getting an article is failed!')
            abort(500)
        finally:
            connection.close()
    return post


@app.route('/metrics')
def metrics():
    connection = get_db_connection()
    post_count = connection.execute('SELECT count(*) FROM posts').fetchone()[0]
    connection.close()

    response = app.response_class(
        response=json.dumps({"db_connection_count": app.config['db_connection_count'], "post_count": post_count}),
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
    posts = None
    connection = get_db_connection()
    # posts = connection.execute('SELECT * FROM posts').fetchall()
    # connection.close()
    if connection:
        try:
            posts = connection.execute('SELECT * FROM posts').fetchall()
        except BaseException:
            logger.error('Getting articles is failed!')
            abort(500)
        finally:
            connection.close()
    return render_template('index.html', posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        logger.error('Non-existing article is accessed!')
        abort(404)
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
            if connection:
                try:
                    connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                                       (title, content))
                    connection.commit()
                    logger.debug('A new article is created!')
                except BaseException:
                    logger.error('Saving a new article is failed!')
                    abort(500)
                finally:
                    connection.close()

            return redirect(url_for('index'))

    return render_template('create.html')


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('500.html'), 500


# Start the application on port 3111
if __name__ == '__main__':
    app.run(host='0.0.0.0', port='3111', debug=True)
