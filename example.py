import os

from noggin.app import App, Response, HTTPError

app = App()

config = {
    'name': 'micropython',
    'url': 'https://micropython.org/',
}

helptext = '''<html>

<h1>About this webapp</h1>

<p>This is a demo webapp. For more information, see
<a href="https://github.com/larsks/noggin">Noggin</a> on
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


@app.route('/get/(.*)')
def get_file(req, match):
    try:
        with open(match.group(1)) as fd:
            return fd.read()
    except OSError:
        raise HTTPError(404)


@app.route('/put/(.*)', method='PUT')
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
        fd.write(req.content)

app.serve()
