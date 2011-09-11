from math import sin,cos,asin,acos,atan2,radians,pi,sqrt
from difflib import get_close_matches
import cPickle as pickle
from data import data

#Earth radius in km
R = 6371.01

def nodetogeo(node):
  nodes=data.nodes
  return {"lat":nodes[node][0],"lng":nodes[node][0]}

def strtoway(streetnames):
  ways=data.ways
  return [w for w in ways if ways[w]['tags'].get('name') in streetnames]

def matchintersection(s):
  """Try to match a string s describing a street intersection to a node (id) of the graph."""
  ways=data.ways
  names=data.names
  if " at q" not in s: return False
  s1,s2=s.split(" at ")[:2]
  s1=s1.strip()
  s2=s2.strip()
  try:
    print "Intersection:",s1,"/",s2
  except:
    pass
  streets1=strtoway(matchstreet(s1))
  streets2=strtoway(matchstreet(s2))
  nodes1={}
  #print streets1
  for i,s in enumerate(streets1):
    for node in ways[s]['n']:
      nodes1[node]=i+1
  nodes2={}
  for i,s in enumerate(streets2):
    for node in ways[s]['n']:
      nodes2[node]=i+1
  intersection={}
  for i,s in enumerate(streets2):
    for node in ways[s]['n']:
      if node in nodes1:
        intersection[node]=nodes1[node]*i
  if len(intersection)==0: return False
  return min(intersection,key=lambda x: intersection[x])

def matchstreet(s1):
  """Try to match a string s1 to the name of a way in the database."""
  names=data.names
  prefixes=[u'Boulevard', u'Parc', u'Croissant', u'rue', u'Chemin', u'Place', u'Rue', u'Avenue', u'Autoroute']
  foundstring=[]
  allmatches=[]
  for p in prefixes:
    matches=get_close_matches(p+" "+s1,names)
    for match in matches:
      if s1 in match:
        foundstring.append(match)
    allmatches+=matches

  if foundstring==[]:
    matches=get_close_matches(s1,names)
    for match in matches:
      if match in allmatches:
        foundstring.append(match)
        
  return foundstring

def nearest(s,sol,nodes,rnodes,G):
  #rnodes=sol[0].keys()
  if s not in rnodes:
    lat=nodes[s][0]
    lon=nodes[s][1]
    return nearestLL((lat,lon),sol,nodes,rnodes,G)

def nearestLL((lat,lon),sol,nodes,rnodes,G):
  """Determine the closest node (id) to a given (lat,lng). Also returns the distance to that node by walking perpendicular to that edge and then along it.

  @param (lat,lon): latitude and longitude of target (end)
  @param sol: the output (D,P,v) to route computed for the source (start)
  @param G: graph
  @param nodes: dictionary {node id:[node lat,node lng]}
  @param rnodes: pre-computed reachable nodes
  """

  try:
    minedge,minxtd,dat,drt=closestStreet((lat,lon),nodes,rnodes,G)
  except:
    return False
  #print minedge
  #print dat+minxtd+sol[0][minedge[0]]
  #print drt+minxtd+sol[0][minedge[1]]
  #print min(dat+minxtd+sol[0][minedge[0]],drt+minxtd+sol[0][minedge[1]])
  if dat+minxtd+sol[0][minedge[0]]<drt+minxtd+sol[0][minedge[1]]:
    return minedge[0],dat+minxtd+sol[0][minedge[0]]
  else:
    return minedge[1],drt+minxtd+sol[0][minedge[1]]
  #return min(dat+minxtd+sol[0][minedge[0]],drt+minxtd+sol[0][minedge[1]])

def insidebb(bbox,pt):
  return (bbox[0]<=pt[0]<=bbox[2] and bbox[1]<=pt[1]<=bbox[3])

def closestNodes(n,nodes,subset=None):
  return closestNodesLL((nodes[n][0],nodes[n][1]),nodes,subset)

def closestNodesLL((lat,lon),nodes,subset=None):
  #print (lat,lon),len(nodes),len(subset)
  #print sorted(subset)[:10]
  #for n in subset:
  #  print nodes[n]
  #  print nodes[n][0]
  if subset is None: subset=nodes.keys()
  order=sorted(subset,key=lambda n: LLdist(lat,lon,nodes[n][0],nodes[n][1]))
  return order

def bearing(lat1,lon1,lat2,lon2):
  dLon=radians(lon2-lon1)
  lat1=radians(lat1)
  lon1=radians(lon1)
  lat2=radians(lat2)
  lon2=radians(lon2)
  y=sin(dLon)*cos(lat2)
  x=cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(dLon)
  #print y,x
  return atan2(y,x)

def LLtovect(lat,lon):
  lat=radians(lat)
  lon=radians(lon)
  x = cos(lat) * cos(lon)
  y = cos(lat) * sin(lon)
  z = sin(lat)
  return [x,y,z]

def vecttoLL((x,y,z)):
  lat = degrees(asin(z))
  lon = degrees(atan2(y, x))
  return (lat,lon)

def xprod(a,b):
  x=a[1]*b[2]-a[2]*b[1]
  y=a[2]*b[0]-a[0]*b[2]
  z=a[0]*b[1]-a[1]*b[0]
  return [x,y,z]

def dprod(v1,v2):
  return sum([v1[i]*v2[i] for i in xrange(len(v1))])

def xtpt(lat1,lon1,lat2,lon2,latmid,lonmid):
  v1=LLtovect(lat1,lon1)
  v2=LLtovect(lat2,lon2)
  vmid=LLtovect(latmid,lonmid)
  N=xprod(v1,v2)
  F=xprod(vmid,N)
  T=xprod(N,F)
  #T=[xi for xi in T]
  #print v1,v2,vmid,N,F,T
  proj=vecttoLL(T)
  dist=LLdist(proj[0],proj[1],latmid,lonmid)
  oncirc=max(LLdist(proj[0],proj[1],lat1,lon1),LLdist(proj[0],proj[1],lat2,lon2))<dist
  return (dist,oncirc)

def bcangle(a,b,c):
  #Need a version that is numerically more stable (e.g., when sin is small)
  try:
    return acos((cos(a) - cos(b)*cos(c))/(sin(b)*sin(c)))
  except:
    return 0

def crosstrackdist(lat1,lon1,lat2,lon2,latmid,lonmid):
  brng13=bearing(lat1,lon1,latmid,lonmid)
  brng12=bearing(lat1,lon1,lat2,lon2)
  dist13=LLdist(lat1,lon1,latmid,lonmid)
  dXt = asin(sin(dist13/R)*sin(brng13-brng12)) * R
  dAt = acos(cos(dist13/R)/cos(dXt/R)) * R
  dist12=LLdist(lat1,lon1,lat2,lon2)
  dist23=LLdist(lat2,lon2,latmid,lonmid)
  #print bcangle(dist13,dist12,dist23)
  #print bcangle(dist23,dist12,dist13)
  oncirc=(bcangle(dist13,dist12,dist23)<pi/2) and (bcangle(dist23,dist12,dist13)<pi/2)
  #print (dXt,dAt,dAt<dist12)
  #print dist12
  return (dXt,dAt,dist12-dAt,oncirc)

def xtdist(n1,n2,latmid,lonmid,nodes):
  return crosstrackdist(nodes[n1][0],nodes[n1][1],nodes[n2][0],nodes[n2][1],latmid,lonmid)

def closestStreet(geo,nodes,subset,G):
  """Returns the closest street from a point geo={'lat':lat,'lng':lon}
  to streets given by G,subset where lat/lon of the subset is specified by nodes
  """

  lat,lon=geo[:2]
  closestnodes=closestNodesLL((lat,lon),nodes,subset)[:10]
  #print lat,lon
  #for n in closestnodes:
  #  print nodes[n][0],nodes[n][1]
  minxtd="" #infinity
  #for i in xrange(len(closestnodes)):
  #  for j in xrange(i+1,len(closestnodes)):
  #    n1=closestnodes[i]
  #    n2=closestnodes[j]
  #    if n1 in G[n2]:
  minedge=None
  for n1 in closestnodes:
    for n2 in G[n1]:
      if n2 in subset:
        xtd,dAt,dRt,oncirc=xtdist(n1,n2,lat,lon,nodes)
        xtd=abs(xtd)

        #also need to check if in between
        if oncirc and xtd<minxtd:
          #Fix rounding errors
          if dRt<0: dRt=0
          minxtd=xtd
          mindat=dAt
          mindrt=dRt
          minedge=(n1,n2)
  if minedge==None: return False
  return (minedge,minxtd,mindat,mindrt)

def distance(data,n1,n2):
  lat1 = data.nodes[n1][0]
  lon1 = data.nodes[n1][1]
  lat2 = data.nodes[n2][0]
  lon2 = data.nodes[n2][1]
  return LLdist(lat1,lon1,lat2,lon2)

def LLdistnode(i,j,nodes):
  return LLdist(nodes[i][0],nodes[i][1],nodes[j][0],nodes[j][1])

def LLdist(lat1,lon1,lat2,lon2):
  dLat = radians(lat2 - lat1)
  dLon = radians(lon2 - lon1)
  a = sin(dLat/2) * sin(dLat/2) + cos(radians(lat1)) * cos(radians(lat2)) * sin(dLon/2) * sin(dLon/2) 
  c = 2 * atan2(sqrt(a), sqrt(1-a))
  d = R * c
  return d
  #dist2 = dlat * dlat + dlon * dlon
  #return(sqrt(dist2))
