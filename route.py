import sys
from utils import *
from priodict import priorityDictionary

def getpath(prev,vert):
  if vert not in prev: return []
  path=[vert]
  while 1:
    if vert not in prev: break
    vert=prev[vert]
    path.append(vert)
  return path

def printpath(Gtags,dist,prev,vert):
  lasttag=None
  while 1:
    print vert,dist[vert]
    if vert not in prev: break
    try:
      if Gtags[vert][prev[vert]]!=lasttag:
        lasttag=Gtags[vert][prev[vert]]
        print lasttag
    except:
      print "Error: tag not found",vert,prev[vert]
      pass
    vert=prev[vert]

def preproute(G,nodes,rnodes,starts,ends=[],Gtags=None):
  """
  Alters the graph G by artificially adding 'starts' and 'ends' nodes that are not in the graph. This is in preparation for routing (we can later route from these new nodes).

  @param G: graph to be altered
  @param nodes: dictionary {node id:[node lat,node lng]}
  @param rnodes: pre-computed reachable nodes
  @param starts: singleton or list of start nodes (each an id or (lat,lng,name) tuple)
  @param ends: singleton or list of end nodes (each an id or (lat,lng,name) tuple)
  @param Gtags: tags of G
  """
  if not type(starts)==list: starts=[starts]
  if not type(ends)==list: ends=[ends]
  newnodes=[]
  for ind,s in enumerate(starts+ends):
    if s not in rnodes:
      #Existing node (but may not be adjacent to any edges so we still have to add it)
      if type(s)==int:
        lat=nodes[s][0]
        lon=nodes[s][1]
      #new node
      else:
        lat,lon,name=s
        s=-ind-1 #new nodes receive negative indices (since we are certain that they are not already in the graph)
        nodes[s]=(lat,lon,name) 
      newnodes.append(s)
      #print "Adding",s
      minedge,minxtd,dat,drt=closestStreet((lat,lon),nodes,rnodes,G)
      #Subdivide an edge of the graph with the new node.
      #To fix: Should add weight consideration if routing by time
      G[s]={minedge[0]:minxtd+dat,minedge[1]:minxtd+drt}
      G[minedge[0]][s]=minxtd+dat
      G[minedge[1]][s]=minxtd+drt
      #Preserve tags of the subdivided edge.
      if Gtags is not None:
        streettags=Gtags[minedge[0]][minedge[1]]
        Gtags[s]={minedge[0]:streettags,minedge[1]:streettags}
        Gtags[minedge[0]][s]=streettags
        Gtags[minedge[1]][s]=streettags
  return newnodes

def route(G,starts,ends=[]):
  """
  Build the shortest path tree in G from starts. Stops when any vertex in 'ends' is met. Uses Dijkstra's algorithm.

  @param G: graph
  @param starts: singleton or list of starting node ids
  @param ends: singleton or list of ending node ids

  @returns: a tuple (D,P,v)
         D: dictionary of distances (from starts)
         P: dictionary of predecessors (encoding the tree)
         v: final vertex (useful to determine which vertex of ends we reached)

  Code modified from the PADS library.
  http://www.ics.uci.edu/~eppstein/PADS/
  """
  D = {}	# dictionary of final distances
  P = {}	# dictionary of predecessors
  Q = priorityDictionary()
  if type(starts)==list:
    for s in starts:
      Q[s]=0
  else:
    Q[starts]=0

  if not type(ends)==list: ends=[ends]

  for v in Q:
    D[v] = Q[v]
    if v in ends: break

    for w in G[v]:
      vwLength = D[v] + G[v][w]
      if w in D:
        if vwLength < D[w]:
          print v,w,vwLength,D[v],G[v][w],D[w]
          raise ValueError, "Dijkstra: found better path to already-final vertex"
      elif w not in Q or vwLength < Q[w]:
        Q[w] = vwLength
        P[w] = v
  return (D,P,v)

if __name__ == "__main__":
  import cPickle as pickle
  if ".pkl" in sys.argv[1]: data = pickle.load(open(sys.argv[1],"rb"))
  else: data = loadOsm(sys.argv[1])

  G=data
  Gtags=pickle.load(open("foottags.pkl","rb"))
  nodes=pickle.load(open("nodes.pkl","rb"))
  rnodes=pickle.load(open("footrnodes.pkl","rb"))

  print "Data loaded"

  preproute(G,nodes,rnodes,int(sys.argv[2]), int(sys.argv[3]),Gtags)
  dist, prev, vert = route(G,int(sys.argv[2]), int(sys.argv[3]))

  print vert,dist[vert]
  lasttag=None
  #Prints path and distance to each intermediate point.
  while 1:
    print vert,dist[vert]
    if vert not in prev: break
    try:
      if Gtags[vert][prev[vert]]!=lasttag:
        lasttag=Gtags[vert][prev[vert]]
        print lasttag
    except:
      print "Error: tag not found",vert,prev[vert]
    vert=prev[vert]

#python route.py footd.pkl 12345 67890
