PROJECT_HOME=$(shell pwd)
PROJECT_ROOT=$(shell dirname "$(PROJECT_HOME)")
BINDIR =${PROJECT_HOME}/bin

SRCDIR = src
DEMODIR = demo

all:
	@for dir in $(SRCDIR) $(DEMODIR); \
	do\
		$(MAKE) -w -C $$dir $@ -k BINDIR=${BINDIR} -k PROJECT_ROOT="${PROJECT_ROOT}"; \
	done

clean:
	@for dir in $(SRCDIR) $(DEMODIR); \
	do\
		$(MAKE) -w -C $$dir $@ -k PROJECT_ROOT="${PROJECT_ROOT}"; \
	done

cleanall: clean
	@$(RM) -f bin/*
