from __future__ import absolute_import

import os
import six

from flask import Flask, redirect, url_for, session
from flask_oauth import OAuth


BASE_URL = os.environ.get('BASE_URL', 'http://localhost:8000')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = '/authorized'

SECRET_KEY = 'development key'
DEBUG = True

app = Flask(__name__)
app.debug = DEBUG
app.secret_key = SECRET_KEY
oauth = OAuth()

sentry = oauth.remote_app(
    'sentry',
    base_url=BASE_URL,
    authorize_url='{}/oauth/authorize/'.format(BASE_URL),
    request_token_url=None,
    request_token_params={
        'scope': 'project:releases event:read org:read org:write',
        'response_type': 'code'
    },
    access_token_url='{}/oauth/token/'.format(BASE_URL),
    access_token_method='POST',
    access_token_params={
        'grant_type': 'authorization_code',
    },
    consumer_key=CLIENT_ID,
    consumer_secret=CLIENT_SECRET,
)


@app.route('/')
def index():
    access_token = session.get('access_token')
    if access_token is None:
        return redirect(url_for('login'))

    from urllib2 import Request, urlopen, URLError
    headers = {'Authorization': 'Bearer {}'.format(access_token)}
    req = Request('{}/api/0/organizations/'.format(BASE_URL),
                  None, headers)
    try:
        res = urlopen(req)
    except URLError, e:
        if e.code == 401:
            # Unauthorized - bad token
            session.pop('access_token', None)
            return redirect(url_for('login'))
        return '{}\n{}'.format(six.text_type(e), e.read())

    return res.read()


@app.route('/login')
def login():
    callback = url_for('authorized', _external=True)
    return sentry.authorize(callback=callback)


@app.route(REDIRECT_URI)
@sentry.authorized_handler
def authorized(resp):
    access_token = resp['access_token']
    session['access_token'] = access_token
    return redirect(url_for('index'))


@sentry.tokengetter
def get_access_token():
    return session.get('access_token')


def main():
    app.run()


if __name__ == '__main__':
    main()
