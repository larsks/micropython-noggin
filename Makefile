PORT = /dev/ttyUSB0
AMPY = ampy -p $(PORT)

CONFIG = config.json
SRCS = \
	noggin/__init__.py \
	noggin/app.py \
	noggin/http.py

all:

check:
	tox

install: .lastinstall

install-example:
	$(AMPY) put example.py

.lastinstall: $(SRCS)
	$(AMPY) mkdir --exists-okay noggin
	for src in $?; do \
		$(AMPY) put $$src $$src; \
	done
	date > .lastinstall

clean:
	rm -f .lastinstall

refresh: clean
	$(AMPY) rmdir tempmonitor
