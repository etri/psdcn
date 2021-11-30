PSDCNv3 CCL API for Python
=======================
    This is Python PubSub API.
    These APIs can work with PSDCNv3 Release-E.   


# Requirements

### python-ndn

    ubuntu 18.04

    $ pip3 install pyndn-ndn

### nest_asyncio

    ubuntu 18.04

    $ pip3 install nest_asyncio


# Running & Debugging

### NFD

    $ nfd-start

### PSDCNv3

    $ cd psdcnv3/scripts
    $ ./start-broker <broker-prefix>
    
### psdcnv3 demo

    $ cd ps-ccl/python

    $ python3 pubdemo.py
    $ python3 subdemo.py

    Adjust svc_name appropriately before you run the demos.

