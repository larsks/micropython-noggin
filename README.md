# Noggin: A very simple web server for MicroPython

## Installation

You need to get the `noggin` directory onto your MicroPython board.  I
like to use the `ampy` command for this:

    ampy -p /dev/ttyUSB0 -b 115200 put noggin

## Overview

Working with Noggin is very simple.  Start by importing a few things
from the module:

    from noggin import Noggin, Response, HTTPError

Create a new Noggin instance:

    app = Noggin()

Define some functions and map them to request paths.  Your function
may return a text value to send that text to the client:

    @app.route('/device/([^/]+)/([^/]+)')
    def device_info(req, dev_type, dev_id):
        return 'You asked about device type {}, device id {}'.format(
            dev_type, dev_id)

Or you can return a dictionary or list to return JSON to the cilent:

    @app.route('/device/([^/]+)/([^/]+)')
    def device_info(req, dev_type, dev_id):
        return {'dev_type': dev_type, 'dev_id': dev_id'}

To run your app, call the `serve` method.  You may optionally provide
a port:

    app.serve(port=8080)

Use the `HTTPError` exception to return errors to the client:

    @app.route('/value/(.*)')
    def get_value(req, sensor):
        if sensor not in active_sensors:
            raise HTTPError(404)

Use the `Response` class if you want to set the returned content type
or other headers:

    @app.route('/')
    def index(req):
        return Response('<strong>This</strong> is a test',
                        mimetype='text/html')

## Examples

### The demo app

Install the demo app. I like to use [ampy][]:

[ampy]: https://github.com/adafruit/ampy

    ampy -p /dev/ttyUSB0 -b 115200 put examples/demo.py demo.py

Now you can run the demo.  On your MicroPython board, import the
example application:

    >>> import demo
    >>> demo.app.serve()

This will start a web server on port 80.  See the docstrings 
[in the source][] for more information about available request
methods.

[in the source]: examples/demo.py

###  The fileops app

The `fileops` app implements a simple web interface to the filesystem.
It supports the following requests:

- `GET /disk` -- get information about the filesystem
- `GET /disk/free` -- get available free space (in blocks and bytes)
- `GET /file` -- get a list of files
- `PUT /file/<path>` -- write a file to the filesystem
- `POST /file/<path>` -- rename a file (new filename is `POST` body)
- `DELETE /file/<path>` -- delete a file
- `GET /reset` -- execute `machine.reset()`

To install the `fileops` app:

    ampy -p /dev/ttyUSB0 -b 115200 put examples/fileops.py fileops.py

To run the `fileops` app:

    >>> import fileops
    >>> fileops.app.serve()
