from urllib import urlencode
from uuid import uuid4
import os

from flask import Flask, request
import requests

app = Flask(__name__)

API_BASE = os.environ.get('API_BASE', 'https://marvelapp.com')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

@app.route('/')
def index():
    connect_url = API_BASE + '/oauth/authorize/?' + urlencode({
        'state': uuid4().hex,
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': 'user:read',
        'redirect_uri': REDIRECT_URI,
    })
    return '<html><a href=%s>Connect with Marvel</a></html>' % connect_url

@app.route('/redirect')
def redirect_handler():
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
