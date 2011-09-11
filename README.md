pygeolib: Python library and CLI for computations on geographical data, with emphasis on algorithms
===================================================================================================

Usage
-----

### Starting with OSM file

You need either some data from [OpenStreetMap](http://wiki.openstreetmap.org/wiki/Downloading_data) or weighted graphs in Python pickle format (second method not yet documented). If starting with OSM maps file.osm, run

    python loadOsm.py file.osm

It is usually a good idea to pick out a single large connected component to work with. Here we pick the one containing the node with id 10000001.

    python build.py graph 10000001

Then, to get the shortest path between nodes numbered `12345` and `67890`, run

    python route.py footd.pkl 12345 67890

More advanced features are not accessible via the command-line interface for the moment. From the python interactive shell,

    $ python

    >>> from route import preproute,route
    >>> from data import data
    >>> sources = [10000001, 10000002, 10000003, 10000005, 10000008]
    >>> newnodes = route.preproute(data.G,data.nodes,data.rnodes,sources)
    >>> newnodes
    [10000001, 10000002, 10000003, 10000005, 10000008]
    >>> D,P,v = route.route(data.G,sources)
    >>> target = 10000013
    >>> D[target]
    19.250000666714794

This is the shortest distance from (the closest of) `10000001, 10000002, 10000003, 10000005, 10000008` to `10000013`.

Any of the sources could also be a `(latitude,longitude,name)` tuple if we want the distance from a non-existent node.

Dependencies
------------

Uses [PADS](http://www.ics.uci.edu/~eppstein/PADS/) (files included)

Originally based on [PyrouteLib](http://wiki.openstreetmap.org/wiki/PyrouteLib) although not much of the library is left.