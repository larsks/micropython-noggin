# Noggin: A very simple web server for MicroPython

## Installation

You need to get the `noggin` directory onto your MicroPython board.  I
like to use the `ampy` command for this:

    ampy -p /dev/ttyUSB0 -b 115200 put noggin

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
- `GET /file` -- get a list of files
- `PUT /file/<path>` -- write a file to the filesystem
- `DELETE /file/<path>` -- delete a file
- `POST /file/<path>' -- rename a file (new filename is `POST` body)

To install the `fileops` app:

    ampy -p /dev/ttyUSB0 -b 115200 put examples/fileops.py fileops.py

To run the `fileops` app:

    >>> import fileops
    >>> fileops.app.serve()
