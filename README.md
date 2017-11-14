# Noggin: A very simple web server for MicroPython

## Installation

You need to get the `noggin` directory onto your MicroPython board.  I
like to use the `ampy` command for this:

    ampy -p /dev/ttyUSB0 -b 115200 put noggin

You may also want to install the example application:

    ampy -p /dev/ttyUSB0 -b 115200 put example.py

Now you can test out the example.  On your MicroPython board, import
the example application:

    >>> import example

Now you can try to contact the server:

    curl http://<your_esp_addr>/

Or retrieve a file:

    curl http://<your_esp_addr>/get/example.py

Or even put a file onto the board:

    curl -T README.md http://<your_esp_addr>/put/README.md
