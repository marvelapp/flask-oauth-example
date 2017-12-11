from urllib import urlencode
from uuid import uuid4
import os

from flask import Flask, request
import requests

app = Flask(__name__)

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

@app.route('/')
def index():
    connect_url = 'https://marvelapp.com/oauth/authorize/?' + urlencode({
        'state': uuid4().hex,
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': 'user:read',
    })
    return '<html><a href=%s>Connect with Marvel</a></html>' % connect_url

@app.route('/redirect')
def redirect_handler():
    # in the real world we should validate that `state` matches the state we set before redirecting the user
    state = request.args.get('state')

    # using the code we've just been given, make a request to obtain
    # an access token for this user
    code = request.args.get('code')
    response = requests.post('https://marvelapp.com/oauth/token/', data={
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
    })
    assert response.ok, 'Token request failed'

    data = response.json()
    token = data['access_token']
    headers = {
        'Authorization': 'Bearer %s' % token,
    }

    # now we can make API requests using this token in the headers
    response = requests.post('https://marvelapp.com/oauth', data='''
        query {
            user {
                email
            }
        }
    ''', headers=headers)

    assert response.ok, 'Request to graphql API failed'
    email = ''
    return '''
        <html>
        <b>%s</b> has authorised their Marvel account
        Their access token is %s
        </html>
    ''' % (email, token)


if __name__ == '__main__':
    app.run(debug=True)
