# PSDCNv2

PSDCNv2
=======
This is PSDCNv2 Software package.


Prerequisites
=============

## install python3

    requires Python >= 3.6
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.6

## install ndn-cxx 0.7.0

    git clone https://github.com/named-data/ndn-cxx
    cd ndn-cxx
    git checkout ndn-cxx-0.7.0

## install NFD 0.7.0

    git clone --recursive https://github.com/named-data/NFD
    cd NFD
    git checkout ndn-cxx-0.7.0

## install python-ndn

    git clone https://github.com/zjkmxy/python-ndn.git

## install redis-nds or redis

    git clone https://github.com/mpalmer/redis.git

## install python modules

    pip install pytest
    pip install pyyaml
    pip install redis
    pip install siphash
    pip install aiofiles
    pip install ratelimit


Running
=======

    nfd-start   
    cd scripts
    ./start-broker [broker name]


Testing
=======

### Using Interactive Tool

    nfd-start   
    cd scripts    
    ./interact    

    > h [enter]


