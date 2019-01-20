import requests
import subprocess
import time

def myDomain():
    '''sp = subprocess.Popen([
        './ngrok',
        'http',
        '-region',
        'ap',
        '5000',
    ])
    '''
    time.sleep(10)

    r = requests.get('http://localhost:4040/api/tunnels')
    json = r.json()
    for i in json['tunnels']:
        if 'https' in i['public_url']:
            url = i['public_url']
    return url
