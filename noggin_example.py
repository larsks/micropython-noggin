import os

from noggin import Noggin, Response, HTTPError

# cribbed from
# https://github.com/micropython/micropython-lib/blob/master/stat/stat.py
S_IFDIR = 0o040000
S_IFMT = 0o170000

app = Noggin()

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
    return Response(content=helptext, mimetype='text/html')


@app.route('/config')
def get_config(req, match):
    '''returning a dictionary (or a list) will send a JSON response
    to the client.'''
    return config


@app.route('/error')
def oops(req, match):
    '''raise HTTPError to send http errors to the client.'''
    raise HTTPError(418)


@app.route('/echo', methods=['PUT', 'POST'])
def echo(req, match):
    '''This will echo content back to the client, but will fail for
    "large" requests because everything is read into memory.'''
    return req.content


@app.route('/yell', methods=['PUT', 'POST'])
def echo(req, match):
    '''Like echo, but implemented with memory-efficient iterables so
    that it should work regardless of the size of the request.'''
    yield from req.iter_content()


@app.route('/disk')
def disk_stats(req, match):
    '''Return information about the filesystem.'''
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


def get_file_list(path):
    '''Recursively list files.

    Returns a list of (name, size, is_dir, children) tuples, where
    children is a similar list of is_dir is True or None of is_dir
    is False.
    '''

    files = []

    for f in os.listdir(path):
        fp = '/'.join([path, f])
        print('* checking', f)
        s = os.stat(fp)
        if s[0] & S_IFMT == S_IFDIR:
            files.append((f, s[6], True, get_file_list(fp)))
        else:
            files.append((f, s[6], False, None))

    return files


@app.route('/file')
def list_files(req, match):
    return get_file_list('/')


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


@app.route('/file/(.*)', methods=['DELETE'])
def del_file(req, match):
    path = match.group(1)
    print('* request to delete {}'.format(path))
    try:
        os.remove(path)
    except OSError:
        raise HTTPError(404)


@app.route('/file/(.*)', methods=['PUT'])
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
