# Noggin: A very simple web server for MicroPython

## Installation

You need to get the `noggin` directory onto your MicroPython board.  I
like to use the `ampy` command for this:

    ampy -p /dev/ttyUSB0 -b 115200 put noggin

## The example app

Install the example:

    ampy -p /dev/ttyUSB0 -b 115200 put noggin_example.py

Now you can test out the example.  On your MicroPython board, import
the example application:

    >>> import noggin_example
    >>> nogging_example.app.serve()

This will start a web server on port 80.

Now you can try to contact the server:

    curl http://<your_esp_addr>/

Or retrieve a file:

    curl http://<your_esp_addr>/file/example.py

Or even put a file onto the board:

    echo this is a test |
    curl -T- http://<your_esp_addr>/file/testfile
