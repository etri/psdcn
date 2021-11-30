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
BINDIR=${PROJECT_HOME}/bin
endif

CFLAGS  += -g -DBOOST_LOG_DYN_LINK
CXXFLAGS    = -g -DBOOST_LOG_DYN_LINK -std=c++14
LFLAGS   = -g

INC      = -I../include -I../../../../rapidjson/include 
LIB     += -L../lib -lpsdcn -lboost_system -lboost_thread -lboost_log -lpthread -lndn-cxx

#PKGS    :=
#CFLAGS += `pkg-config --cflags $(PKGS)`
#LIB+= `pkg-config --libs $(PKGS)`

#INC        = $(shell pkg-config --cflags json-c)
#LIB        = -Wl,-Bstatic $(shell pkg-config --libs json-c) -Wl,-Bdynamic -Wl,-lcurl

INCS:= $(wildcard *.hpp)

PUBOBJS = pubdemo.o 
SUBOBJS = subdemo.o
SUBLOBJS = subldemo.o

TARGET=pubdemo subdemo # subldemo

all: $(BINDIR) $(TARGET)
	$(RM) -f $(PUBOBJS) $(SUBOBJS) $(SUBLOBJS)

pubdemo: $(BINDIR) $(PUBOBJS)
	$(CXX) -o $(@:%=${BINDIR}/%) $(LFLAGS) $(PUBOBJS) $(LIB)
	cd $(BINDIR); rm -f publocal; ln $@ publocal

subdemo: $(BINDIR) $(SUBOBJS)
	$(CXX) -o $(@:%=${BINDIR}/%) $(LFLAGS) $(SUBOBJS) $(LIB)

subldemo: $(BINDIR) $(SUBLOBJS)
	$(CXX) -o $(@:%=${BINDIR}/%) $(LFLAGS) $(SUBLOBJS) $(LIB)

.SUFFIXES : .cpp .c .o
.cpp.o:
	$(CXX) -o $@ $(CXXFLAGS) $(INC) -c $<

clean:
	$(RM) -f *.o

$(BINDIR):
	mkdir -p $(BINDIR)

