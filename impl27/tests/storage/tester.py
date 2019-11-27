def test(storage):
    k1 = '/etri/bldg7/room513/temperature'
    v1 = 30
    k2 = '/etri/bldg3/room628/switches'
    v2 = ('off', 'on', 'off')
    k3 = '/etri/bldg7/room513/main-switch'
    v3 = 'off'
    ks = '/etri/bldg6/room101/printers'
    vs = {'color': ['hp'], 'bw': ['canon', 'epson', 'lg']}
    
    print storage.mset(k1, v1, k2, v2, k3, v3), 3
    print storage.get(k2), v2
    print storage.mget(k3, k1), [v3, v1]
    print storage.delete(k1), 1
    print storage.get(k1), None
    print storage.delete(k1), 0
    print storage.set(ks, vs), 1
    print storage.get(ks), vs
    print storage.flush(), 3

