CC=$(CROSS_COMPILE)gcc
CXX=$(CROSS_COMPILE)g++
AR=$(CROSS_COMPILE)ar
LD=$(CROSS_COMPILE)ld
NM=$(CROSS_COMPILE)nm
STRIP=$(CROSS_COMPILE)strip
RM=rm
RMDIR=rmdir

ifeq ("$(PROJECT_HOME)", "")
PROJECT_HOME=$(shell dirname $(shell pwd))
LIBDIR=${PROJECT_HOME}/lib
OUTDIR=out
endif

CFLAGS  += -g -DBOOST_LOG_DYN_LINK
CXXFLAGS    = -g -DBOOST_LOG_DYN_LINK -std=c++14 -fPIC
LFLAGS   = -g

INC	= -I../include -I../../../../rapidjson/include 

LIBDIR   = ../lib
LIB	= $(LIBDIR)/libpsdcn.so.0.0.0

#PKGS    :=
#CFLAGS += `pkg-config --cflags $(PKGS)`
#LIB+= `pkg-config --libs $(PKGS)`

#INC        = $(shell pkg-config --cflags json-c)
#LIB        = -Wl,-Bstatic $(shell pkg-config --libs json-c) -Wl,-Bdynamic -Wl,-lcurl

INCS := $(wildcard *.hpp)

OBJS = pubsub.o \
	pskcmd.o \
	pubadvinfo.o \
	pubdatainfo.o \
	irinfo.o \
	subinfo.o \
	logging.o

TARGET= lib

all: $(TARGET) install

lib:	$(LIBDIR) $(OBJS)
	$(CXX) -shared -Wl,-soname,libpsdcn.so.0 -o $(LIB) $(OBJS)

install: $(TARGET)
	@echo
	@echo "Installing psdcn libraries..."
	-sudo rm -f /usr/local/lib/libpsdcn.so*
	-cd $(LIBDIR); sudo cp libpsdcn.so.0.0.0 /usr/local/lib
	-cd /usr/local/lib; sudo ln -s $(LIB) libpsdcn.so.0
	-cd /usr/local/lib; sudo ln -s $(LIB) libpsdcn.so
	-sudo ldconfig


.SUFFIXES : .cpp .c .o
#.c.o:
$(OUTDIR)/%.o:%.c $(INCS)
	$(CC) -o $@ $(CFLAGS) $(INC) -c $<
#$(OUTDIR)/%.o:%.cpp $(INCS)
.cpp.o:
	$(CXX) -o $@ $(CXXFLAGS) $(INC) -c $<

clean:
	$(RM) -f $(OBJS) $(LIB)

$(LIBDIR):
	mkdir -p $(LIBDIR)

