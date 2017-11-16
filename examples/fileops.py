try:
    import binascii
except ImportError:
    import ubinascii as binascii

import errno
import gc
import machine
import network
import os

from noggin import Noggin, Response, HTTPError

# cribbed from
# https://github.com/micropython/micropython-lib/blob/master/stat/stat.py
S_IFDIR = 0o040000
S_IFMT = 0o170000

app = Noggin()


def chunked_iter(path):
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


@app.route('/')
def index(req):
    return Response(content=chunked_iter('help.html'),
                    content_type='text/html')


def get_statvfs():
    statvfs_fields = [
        'bsize',
        'frsize',
        'blocks',
        'bfree',
        'bavail',
        'files',
        'ffree',
    ]
    return dict(zip(statvfs_fields, os.statvfs('/')))


@app.route('/disk')
def disk_stats(req):
    '''Return information about the filesystem.'''
    return get_statvfs()


@app.route('/disk/free')
def disk_free(req):
    '''Return available space'''
    s = get_statvfs()
    return {
        'blocks': s['bfree'],
        'bytes': (s['bsize'] * s['bfree'])
    }


@app.route('/mem/free')
def mem_free(req):
    '''Return available memory'''
    return {
        'bytes': gc.mem_free()
    }


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
def list_files(req):
    '''Return a list of files'''
    return get_file_list('/')


@app.route('/file/(.*)')
def get_file(req, path):
    '''Retrieve file contents'''
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
def del_file(req, path):
    '''Delete a file'''
    print('* request to delete {}'.format(path))
    try:
        os.remove(path)
    except OSError as err:
        if err.args[0] == errno.ENOENT:
            raise HTTPError(404)
        else:
            raise HTTPError(500)


@app.route('/file/(.*)', methods=['POST'])
def rename_file(req, path):
    '''Rename a file'''
    newpath = req.text
    print('* request to rename {} -> {}'.format(path, newpath))
    try:
        os.rename(path, newpath)
    except OSError as err:
        if err.args[0] == errno.ENOENT:
            raise HTTPError(404)
        else:
            raise HTTPError(500)


@app.route('/file/(.*)', methods=['PUT'])
def put_file(req, path):
    '''Create or replace a file.'''
    print('* request to put {}'.format(path))
    parts = path.split('/')

    for i in range(len(parts) - 1):
        partial = '/'.join(parts[:i + 1])
        print('* create directory {}'.format(partial))
        try:
            os.mkdir(partial)
        except OSError:
            pass

    with open(path, 'w') as fd:
        for chunk in req.iter_content():
            fd.write(chunk)


@app.route('/reset')
def reset(req):
    '''Reset the board (via machine.reset)'''
    req.close()
    machine.reset()


@app.route('/net/([^/]+)(/([^/]+))?')
def get_net_info(req, iface_name, _, key):
    '''Get information about a network interface.

    "eth0" or "sta" refers to the wireless client interface.
    "eth1" or "ap" refers to the wireless access point interface.
    '''
    print('* net info request for {} {}'.format(iface_name, repr(key)))

    try:
        iface_num = {
            'sta': network.STA_IF,
            'eth0': network.STA_IF,
            'ap': network.AP_IF,
            'eth1': network.AP_IF,
        }[iface_name]
        iface = network.WLAN(iface_num)
        netinfo = dict(zip(['addr', 'mask', 'gateway', 'dns'],
                           iface.ifconfig()))

        netinfo['active'] = iface.active()
        netinfo['connected'] = iface.isconnected()
        mac = iface.config('mac')
        netinfo['mac'] = binascii.hexlify(mac).decode('ascii')

        if key:
            try:
                return str(netinfo[key])
            except KeyError:
                return str(iface.config(key))
        else:
            return netinfo
    except KeyError as err:
        raise HTTPError(404, None, 'Unknown key: {}'.format(err))
    except ValueError as err:
        raise HTTPError(500, None, 'Bad request: {}'.format(err))
