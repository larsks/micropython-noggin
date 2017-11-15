PORT = /dev/ttyUSB0
AMPY = ampy -p $(PORT)
MPYCROSS = mpy-cross

CONFIG = config.json
SRCS = \
	noggin/__init__.py \
	noggin/app.py \
	noggin/http.py

EXAMPLES = \
	examples/demo.py \
	examples/fileops.py

OBJS = $(SRCS:.py=.mpy)

EXOBJS = $(EXAMPLES:.py=.mpy)

%.mpy: %.py
	$(MPYCROSS) $<

all: $(OBJS) $(EXOBJS)

check:
	tox

install: .lastinstall

install-examples: .lastinstall-examples

.lastinstall: $(OBJS)
	$(AMPY) mkdir --exists-okay noggin
	for src in $?; do \
		$(AMPY) put $$src $$src; \
	done
	date > $@

.lastinstall-examples: $(EXOBJS) examples/help.html
	for src in $?; do \
		$(AMPY) put $$src `basename $$src`; \
	done
	date > $@

clean:
	rm -f .lastinstall $(OBJS)

refresh: clean
	$(AMPY) rmdir tempmonitor
