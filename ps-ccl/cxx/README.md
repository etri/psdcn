PSDCNv3 CCL API for C++
=======================
    This is C++ PubSub API.
    These APIs can work with PSDCNv3 Release-E.   


# Requirements

### ndn-cxx
    ndn-cxx 0.7.1
    
### rapidjson

    ubuntu 18.04

    $ sudo apt-get install rapidjson-dev

# Compiling

    $ git clone https://etrioss.kr/tuple/psdcnv3.git
    $ cd psdcnv3/ps-ccl/cxx
    $ make install
    $ sudo ldconfig


# Running & Debugging

### NFD

    $ nfd-start

### PSDCNv3

    $ cd psdcnv3/scripts
    $ ./start-broker <broker-prefix>
    
### psdcnv3 demo

    $ export NDN_LOG=psdcn.*=DEBUG
    $ bin/pubdemo

    $ export NDN_LOG=psdcn.*=DEBUG
    $ bin/subdemo

    $ export NDN_LOG=psdcn.*=DEBUG
    $ bin/subdemol	# for sublocal demos

    Adjust svc_name appropriately before you build demos.

