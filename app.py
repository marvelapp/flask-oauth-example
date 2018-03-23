from urllib import urlencode
from uuid import uuid4
import os
import hashlib
from base64 import urlsafe_b64encode

from flask import Flask, request, session
import requests

app = Flask(__name__)
app.secret_key = os.urandom(20).encode('base64')


API_BASE = os.environ.get('API_BASE', 'https://api.marvelapp.com')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

@app.route('/')
def index():
    code_verifier = os.urandom(64).encode('base64')
    code_challenge = urlsafe_b64encode(hashlib.sha256(code_verifier).hexdigest())
    connect_url = API_BASE + '/oauth/authorize/?' + urlencode({
        'state': uuid4().hex,
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': 'user:read',
        'redirect_uri': REDIRECT_URI,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    })
    session['code_verifier'] = code_verifier
    session.modified = True
    return '<html><a href=%s>Connect with Marvel</a></html>' % connect_url

@app.route('/redirect')
def redirect_handler():
    assert 'error' not in request.args, request.args

    # in the real world we should validate that `state` matches the state we set before redirecting the user
    state = request.args.get('state')

    # using the code we've just been given, make a request to obtain
    # an access token for this user
    code = request.args.get('code')
    response = requests.post(API_BASE + '/oauth/token/', data={
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': session['code_verifier'],
    })
    assert response.ok, 'Token request failed: %s' % response.content

    data = response.json()
    token = data['access_token']
    headers = {
        'Authorization': 'Bearer %s' % token,
    }

    # now we can make API requests using this token in the headers
    response = requests.post(API_BASE + '/graphql', json={
        'query': '''
            query {
                user {
                    email
                }
            }
        '''
    }, headers=headers)

    assert response.ok, 'Request to graphql API failed'

    email = response.json()['data']['user']['email']
    return '''
        <html>
        %s has authorised their Marvel account
        Their access token is %s
        </html>
    ''' % (email, token)


if __name__ == '__main__':
    app.run(debug=True)
