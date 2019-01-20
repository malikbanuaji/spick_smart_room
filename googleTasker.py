import requests
import os
import subprocess
import pathlib
import magic

#s = request.Session()

#r = s.get('https://docs.google.com/document/export?format=pdf&id=1xCE6bf8KgTqn6o0XfT9ZQ_gmKM4-lqCK8t0Lj00GJTA')
#link = 'https://docs.google.com/presentation/d/1CJ202xuX6QX3b8LuIp-QNa5mYestha2mGigsJZDfv5k/edit?usp=sharing'
#link = 'https://docs.google.com/presentation/u/0/d/1CJ202xuX6QX3b8LuIp-QNa5mYestha2mGigsJZDfv5k/export/odp?id=1CJ202xuX6QX3b8LuIp-QNa5mYestha2mGigsJZDfv5k&pageid=p'

#link2 = 'https://docs.google.com/document/d/1xCE6bf8KgTqn6o0XfT9ZQ_gmKM4-lqCK8t0Lj00GJTA/edit'
#link3 = 'https://docs.google.com/document/export?format=pdf&id=1xCE6bf8KgTqn6o0XfT9ZQ_gmKM4-lqCK8t0Lj00GJTA'

#r = requests.get(link)

#filename = ''
mime = magic.Magic(mime=True)

def googleDriveExport(link_id, fileType):

    if fileType == 'presentation':
        filename = 'presentation.odp'
        link = 'https://docs.google.com/presentation/d/{}/export/odp?id={}&pageid=p'.format(link_id, link_id)
        #link = 'https://docs.google.com/presentation/d/{}/export/odp/?id={}&pageid=p'.format(link_id, link_id)
        link_d = 'https://docs.google.com/presentation/d/{}/export/odp?id={}&pageid=p1'.format(link_id, link_id)
        #https://docs.google.com/presentation/d/1J6-986x0KVBc2l9f_qY-A4JCW_AWD38_58YyZOAAfdI/export/odp?id=1J6-986x0KVBc2l9f_qY-A4JCW_AWD38_58YyZOAAfdI&pageid=p
        task = 'presentation'
        type = Downloader(filename, link)
        if 'text/html' in type:
            print('file type is wrong, redownload with new link')
            Downloader(filename, link_d)

    elif fileType == 'document':
        filename = 'document.pdf'
        link = 'https://docs.google.com/document/export?format=pdf&id={}'.format(link_id)
        task = 'print'

    return os.path.abspath(filename)

def Downloader(filename, link):
    global mime
    r = requests.get(link)
    with open(os.path.abspath(filename), 'wb') as f:
        for chunk in r.iter_content(chunk_size = 2048):
            f.write(chunk)

    while pathlib.Path(filename).is_file() == False:
        time.sleep(1)

    print('file has been downloaded')
    return mime.from_file(os.path.abspath(filename))
