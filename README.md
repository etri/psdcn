A Scalable Broker System for Pub/Sub over DCN(Data Centric Network)
========================
    # PSDCN git clone

    git clone https://github.com/etri/psdcn.git
    cd psdcn

Prerequisites
=============

    # Tested under Ubuntu 16.04.05

    # Python2
   
    sudo apt-get install python-dev python-pip
    pip install gevent
    
Functional Test
=============

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

