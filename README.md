# Noggin: A very simple web server for MicroPython

## Installation

You need to get the `noggin` directory onto your MicroPython board.  I
like to use the `ampy` command for this:

    ampy -p /dev/ttyUSB0 -b 115200 put noggin

## Examples

### The demo app

Install the example:

    ampy -p /dev/ttyUSB0 -b 115200 put examples/demo.py demo.py

Now you can test out the example.  On your MicroPython board, import
the example application:

    >>> import demo
    >>> demo.app.serve()

This will start a web server on port 80.

###  The fileops app

The `fileops` app implements a simple web interface to the filesystem.
It supports the following requests:

- `GET /disk` -- get information about the filesystem
- `GET /file` -- get a list of files
- `PUT /file/<path>` -- write a file to the filesystem
- `DELETE /file/<path>` -- delete a file

To install the `fileops` app:

    ampy -p /dev/ttyUSB0 -b 115200 put examples/fileops.py fileops.py

To run the `fileops` app:

    >>> import fileops
    >>> fileops.app.serve()
