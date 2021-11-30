PSDCNv3
=======
This is PSDCNv3 Software package.


Prerequisites
=============

### install python3

    requires Python >= 3.8

### install ndn-cxx 0.7.1

    git clone https://github.com/named-data/ndn-cxx
    cd ndn-cxx
    git checkout ndn-cxx-0.7.1

### install NFD 0.7.1

    git clone --recursive https://github.com/named-data/NFD
    cd NFD
    git checkout ndn-cxx-0.7.1

### install python-ndn

    git clone https://github.com/zjkmxy/python-ndn.git

### install redis-nds or redis

    git clone https://github.com/mpalmer/redis.git

### install python modules

    sudo apt install python3.8-dev
    pip3 install pyyaml
    pip3 install redis
    pip3 install siphash
    pip3 install aiofiles
    pip3 install ratelimit
    pip3 install psutil

### install optional python modules

    pip3 install pytest (for running testcases)


Running
=======

    cd scripts
    ./nfd-restart
    ./start-broker [broker name]


Testing
=======

### Using interactive testing tool

    cd scripts    
    ./nfd-restart
    ./interact    

    > h [enter]

### Demos

    Some demo scripts are under demo/scripts

### Testcases

    Functional and performance tests are under tests

