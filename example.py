import os

from noggin.app import App, Response, HTTPError

# cribbed from
# https://github.com/micropython/micropython-lib/blob/master/stat/stat.py
S_IFDIR = 0o040000
S_IFMT = 0o170000

app = App()

config = {
    'name': 'micropython',
    'url': 'https://micropython.org/',
}

helptext = '''<html>

<h1>About this webapp</h1>

<p>This is a demo webapp. For more information, see
<a href="https://github.com/larsks/micropython-noggin">Noggin</a> on
GitHub.</p>

</html>'''


@app.route('/')
def index(req, match):
    return 'Hello world!'


@app.route('/help')
def get_help(req, match):
    return Response(content=helptext, mimetype='text/html')


@app.route('/config')
def get_config(req, match):
    return config


@app.route('/error')
def oops(req, match):
    raise HTTPError(418)


@app.route('/echo', method='PUT')
def echo(req, match):
    return req.content


@app.route('/disk')
def disk_stats(req, match):
    statvfs_fields = [
        'sb.f_bsize',
        'sb.f_frsize',
        'sb.f_blocks',
        'sb.f_bfree',
        'sb.f_bavail',
        'sb.f_files',
        'sb.f_ffree',
    ]
    return dict(zip(statvfs_fields, os.statvfs('/')))


@app.route('/file/(.*)')
def get_file(req, match):
    path = match.group(1)
    print('* request to get {}'.format(path))
    buf = bytearray(256)
    try:
        with open(path) as fd:
            while True:
                nb = fd.readinto(buf)
                if not nb:
                    break
                yield buf[:nb]
    except OSError:
        raise HTTPError(404)


@app.route('/file/(.*)', method='DELETE')
def del_file(req, match):
    path = match.group(1)
    print('* request to delete {}'.format(path))
    try:
        os.remove(path)
    except OSError:
        raise HTTPError(404)


@app.route('/file/(.*)', method='PUT')
def put_file(req, match):
    path = match.group(1)
    print('* request to put {}'.format(path))
    parts = path.split(b'/')

    for i in range(len(parts) - 1):
        partial = b'/'.join(parts[:i + 1])
        print('* create directory {}'.format(partial))
        try:
            os.mkdir(partial)
        except OSError:
            pass

    with open(path, 'w') as fd:
        for chunk in req.iter_content():
            fd.write(chunk)

app.serve()
