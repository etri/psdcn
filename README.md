A Scalable Broker System for Pub/Sub over DCN(Data Centric Networking)
========================================================================
    # PSDCN git clone

    git clone https://github.com/etri/psdcn.git
    cd psdcn

Prerequisites
=============

    # Tested under Ubuntu 16.04.05

    # Python2
   
    sudo apt-get install python-dev python-pip
    pip install gevent
    
    # Tested under Ubuntu 18.04.4
    
    # Python3 
    sudo apt-get update -y
    sudo apt-get install -y python3.6-gevent

Functional Test for Broker
==========================

    # Use impl27/tests directory for functional test under Python2

    # broker test
    cd impl27/tests/broker
    python local.py

    # storage test
    cd ../storage
    python memory.py
    python protocol.py
 
    # topic test
    cd ../topics
    python functions.py
    python perf1.py  (perf1.py ~ perf9.py)
    python performance.py

    # Use impl36/tests directory for functional test under Python3

    # broker test
    cd impl36/tests/broker
    python3 local.py

    # storage test
    cd ../storage
    python3 memory.py
    python3 protocol.py
 
    # topic test
    cd ../topics
    python3 functions.py
    python3 perf1.py  (perf1.py ~ perf9.py)
    python3 performance.py

