#!/usr/bin/python
#----------------------------------------------------------------
# load OSM data file into memory
#
#------------------------------------------------------
# Usage: 
#   data = LoadOsm(filename)
# or:
#   loadOsm.py filename.osm
#------------------------------------------------------
# Copyright 2007, Oliver White
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#------------------------------------------------------
# Changelog:
#  2007-11-04  OJW  Modified from pyroute.py
#  2007-11-05  OJW  Multiple forms of transport
#  2010-07-25  zl   Now storing much more information. Saves output to pkl files
#------------------------------------------------------
import sys
import os
from xml.sax import make_parser, handler
from utils import distance
from weights import *

class LoadOsm(handler.ContentHandler):
  """Parse an OSM file looking for routing information, and do routing with it"""
  def __init__(self, filename, storeMap = 0):
    """Initialise an OSM-file parser"""
    self.routing = {}
    self.routeTypes = ('cycle','car','train','foot','horse')
    self.routeableNodes = {}
    for routeType in self.routeTypes:
      self.routing[routeType] = {}
      self.routing[routeType]["d"] = {} #distance
      #time (distance weighted by weights.py), mostly for walking time
      self.routing[routeType]["t"] = {}
      self.routing[routeType]["tags"] = {}
      self.routeableNodes[routeType] = {}
    self.nodes = {}
    self.ways = {}
    self.relations = {}
    self.relmembers = {}
    self.storeMap = storeMap
    self.tags = {}
    self.id = -1

    if(filename == None):
      return
    self.loadOsm(filename)
    
  def loadOsm(self, filename):
    if(not os.path.exists(filename)):
      print "No such data file %s" % filename
      return
    try:
      parser = make_parser()
      parser.setContentHandler(self)
      parser.parse(filename)
    except xml.sax._exceptions.SAXParseException:
      print "Error loading %s" % filename

  def startElement(self, name, attrs):
    """Handle XML elements"""
    if name in('node','way','relation'):
      if name == 'node':
        """Nodes need to be stored"""
        id = int(attrs.get('id'))
        lat = float(attrs.get('lat'))
        lon = float(attrs.get('lon'))
        self.nodes[id] = [lat,lon]
      self.id = int(attrs.get('id'))
      self.tags = {}
      self.waynodes = []
      self.relmembers = []
    elif name == 'nd':
      """Nodes within a way -- add them to a list"""
      self.waynodes.append(int(attrs.get('ref')))
    elif name == 'member':
      self.relmembers.append((attrs.get('type'),int(attrs.get('ref')),attrs.get('role')))
    elif name == 'tag':
      """Tags - store them in a hash"""
      k,v = (attrs.get('k'), attrs.get('v'))
      if not k in ('created_by'):
        self.tags[k] = v

  def endElement(self, name):
    """Handle ways in the OSM data"""
    if name == 'way':
      highway = self.equivalent(self.tags.get('highway', ''))
      railway = self.equivalent(self.tags.get('railway', ''))
      oneway = self.tags.get('oneway', '')
      reversible = not oneway in('yes','true','1')

      # Calculate what vehicles can use this route
      access = {}
      access['cycle'] = highway in ('primary','secondary','tertiary','unclassified','minor','cycleway','residential', 'track','service')
      access['car'] = highway in ('motorway','trunk','primary','secondary','tertiary','unclassified','minor','residential', 'service')
      access['train'] = railway in('rail','light_rail','subway')
      access['foot'] = (access['cycle'] and self.tags.get("lcn")!="yes") or highway in('footway','steps')
      access['horse'] = highway in ('track','unclassified','bridleway')
      
      # Store routing information
      if (self.tags.get("building") != "yes"):
        for routeType in self.routeTypes:
          if access[routeType]:
            if ("leisure" not in self.tags):
              pairs=[(i-1,i) for i in xrange(1,len(self.waynodes))]
            else:
              #Park or some such, so add a clique
              pairs=[(i,j) for i in xrange(len(self.waynodes)) for j in xrange(i+1,len(self.waynodes))]
            for i,j in pairs:
              last = self.waynodes[i]
              current = self.waynodes[j]
              if last in self.nodes and current in self.nodes:
                weight = getWeight(routeType, highway)
                if weight > 0:
                  dist = distance(self,last,current)
                  self.addLink(last, current, routeType,"d",dist)
                  self.addLink(last, current, routeType,"t",dist/weight)
                  self.addLink(last, current, routeType,"tags",self.tags)
                  if reversible or routeType == 'foot':
                    self.addLink(current, last, routeType,"d",dist)
                    self.addLink(current, last, routeType,"t",dist/weight)
                    self.addLink(current, last, routeType,"tags",self.tags)
          
      # Store map information
      if(self.storeMap):
        wayType = self.WayType(self.tags)
        if(wayType):
          self.ways[self.id]={'t':wayType, 'n':self.waynodes, 'tags':self.tags}
    elif name == 'relation':
      if(self.storeMap):
        self.relations[self.id]={'tags':self.tags, 'members':self.relmembers}
    elif name == 'node':
      self.nodes[self.id].append(self.tags)

  def addLink(self,fr,to, routeType, subtype, weight=1):
    """Add a routeable edge to the scenario"""
    self.routeableNodes[routeType][fr] = 1
    #if subtype not in self.routing[routeType]: self.routing[routeType][subtype]={}
    if fr in self.routing[routeType][subtype]:
      if to in self.routing[routeType][subtype][fr]:
        self.routing[routeType][subtype][fr][to]=min(weight,self.routing[routeType][subtype][fr][to])
      else:
        self.routing[routeType][subtype][fr][to] = weight
    else:
      self.routing[routeType][subtype][fr] = {to: weight}

  def WayType(self, tags):
    # Look for a variety of tags (priority order - first one found is used)
    for key in ('highway','railway','waterway','natural'):
      value = tags.get(key, '')
      if value:
        return(self.equivalent(value))
    return('unidentified')
  def equivalent(self,tag):
    """Simplifies a bunch of tags to nearly-equivalent ones"""
    equivalent = { \
      "primary_link":"primary",
      "trunk":"primary",
      "trunk_link":"primary",
      "secondary_link":"secondary",
      "tertiary":"secondary",
      "tertiary_link":"secondary",
      "residential":"unclassified",
      "minor":"unclassified",
      "steps":"footway",
      "driveway":"service",
      "pedestrian":"footway",
      "bridleway":"cycleway",
      "track":"cycleway",
      "arcade":"footway",
      "canal":"river",
      "riverbank":"river",
      "lake":"river",
      "light_rail":"railway"
      }
    try:
      return(equivalent[tag])
    except KeyError:
      return(tag)
    

  def writepickle(data):
    """Write loaded data to the following pickle files
    @param data: data from loadOsm

    G.pkl - the graph (dictionary {node id:[neighbour of node]})
    nodes.pkl - dictionary {node id:[node lat,node lng]}
    ways.pkl - dictionary {edge id:{'t':edge type,
                                    'n':edge nodes,
                                    'tags':edge tags}}
    relations.pkl - dictionary {relation id:{'tags':relation tags,
                                            'members':relation members}}
    footrnodes - routable (reachable) nodes by foot
    footd.pkl - subgraph of G.pkl with only foot accessible edges
                and distances as weights
    foott.pkl - subgraph of G.pkl with only foot accessible edges
                and time as weights
    foottags.pkl - subgraph of G.pkl with only foot accessible edges
                   and tags as weights

    All id's are integers.
    """

    import cPickle as pickle
    pickle.dump(data,open("G.pkl","wb"))
    pickle.dump(data.nodes,open("nodes.pkl","wb"))
    pickle.dump(data.ways,open("ways.pkl","wb"))
    pickle.dump(data.relations,open("relations.pkl","wb"))
    pickle.dump(data.routeableNodes["foot"],open("footrnodes.pkl","wb"))
    pickle.dump(data.routing["foot"]["d"],open("footd.pkl","wb"))
    pickle.dump(data.routing["foot"]["t"],open("foott.pkl","wb"))
    pickle.dump(data.routing["foot"]["tags"],open("foottags.pkl","wb"))

# Parse the supplied OSM file
if __name__ == "__main__":
  if len(sys.argv)<2:
    print """
python loadOsm.py [FILE]
  Loads a .osm file FILE and produces pickled (.pkl) files containing the graph and other information to be used by other tools.
"""
    sys.exit(0)
  print "Loading data..."
  data = LoadOsm(sys.argv[1], True)
  print "Data loaded"
  del data.__dict__['_locator']

  data.writepickle()
