import sys
from utils import *
import cPickle as pickle
from route import *
from data import data

def buildconn(nn):
    """Build a connected component starting from nn and saves this component in the file conncomp.pkl"""
    G=data.G
    sol=route(G,nn)
    print "Saving solution to conncomp.pkl"
    pickle.dump(sol[0],open("conncomp.pkl","wb"))

def buildtrees(targets):
    G=data.G
    nodes=data.nodes
    rnodes=data.rnodes
    print "Buliding shortest paths to targets"
    preproute(G,nodes,rnodes,targets)
    sol=route(G,targets)
    print "Saving solution to targetsol.pkl and targetnodes.pkl"
    pickle.dump(sol,open("targetsol.pkl","wb"))
    pickle.dump(nodes,open("targetnodes.pkl","wb"))

def buildstreetnames():
    ways=data.ways
    names=[]
    for k in ways:
        name=ways[k]['tags'].get('name')
        if name is not None:
            names.append(name)
    pickle.dump(names,open("streetnames.pkl","wb"))
    return names

def buildprefixes():
    names=data.names
    prefixes=[n.split()[0] for n in names]
    freqprefixes=set([p for p in prefixes if prefixes.count(p)>50])
    #postfixes=[n.split()[0] for n in names]
    #freqpostfixes=set([p for p in postfixes if postfixes.count(p)>50])
    return freqprefixes

if __name__=="__main__":
    if sys.argv[1] in ["conn","graph"]:
        if len(sys.argv)<2:
            print "Missing argument node number"
            sys.exit(1)
        else:
            try:
                nn=int(sys.argv[2])
            except:
                print "Error: parsing sys.argv[2]"
                sys.exit(1)
            G=data.G
            if nn not in G:
                print "Error: "+str(nn)+" is not in the graph."
                sys.exit(1)
            print "Building graph starting from "+str(nn)
            buildconn(nn)
    elif sys.argv[1] in ["street","streetname"]:
        buildstreetnames()
    elif sys.argv[1] in ["tree","trees"]:
        targets = pickle.load(sys.argv[2])
        rnodes = data.rnodes
        buildtrees(targets)
    else:
        print sys.argv[1]+" is an unrecognized command"
