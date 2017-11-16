from noggin import Noggin, Response, HTTPError

app = Noggin()

helptext = '''<html>

<h1>About this webapp</h1>

<p>This is a demo webapp. For more information, see
<a href="https://github.com/larsks/micropython-noggin">Noggin</a> on
GitHub.</p>

</html>'''


@app.route('/')
def index(req):
    '''Return text to send it to the client'''
    return 'This is the Noggin demo app.\n'


@app.route('/help')
def get_help(req):
    '''Return a Response object if you need to set the content-type or
    other headers'''
    return Response(content=helptext, content_type='text/html')


@app.route('/json')
def get_json(req):
    '''returning a dictionary (or a list) will send a JSON response
    to the client.'''
    return {
        'word': 'noggin',
        'definition': ('a small quantity of liquor, '
                       'typically a quarter of a pint.')
    }


@app.route('/error')
def error(req):
    '''raise HTTPError to send http errors to the client.'''
    raise HTTPError(418)


@app.route('/echo1', methods=['PUT', 'POST'])
def echo1(req):
    '''This will echo content back to the client, but will fail for
    "large" requests because everything is read into memory.'''
    return req.content


@app.route('/echo2', methods=['PUT', 'POST'])
def echo2(req):
    '''Like echo1, but implemented with memory-efficient iterables so
    that it should work regardless of the size of the request.'''
    yield from req.iter_content()


@app.route('/device/([^/]+)/([^/]+)')
def parameters(req, p1, p2):
    '''Match groups in the route will be passed to your function as
    positional parameters.'''

    return {'p1': p1, 'p2': p2}
