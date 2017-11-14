PORT = /dev/ttyUSB1
AMPY = ampy -p $(PORT)

CONFIG = config.json
SRCS = \
	noggin/__init__.py \
	noggin/app.py \
	noggin/http.py

all:

check:
	tox

install: .lastbuild

.lastbuild: $(SRCS)
	$(AMPY) mkdir --exists-okay noggin
	for src in $?; do \
		$(AMPY) put $$src $$src; \
	done
	date > .lastbuild

clean:
	rm -f .lastbuild

refresh: clean
	$(AMPY) rmdir tempmonitor
