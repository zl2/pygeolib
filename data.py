import cPickle as pickle
class Data:
    _data={}
    filenames={"names":"streetnames.pkl",
               "ways":"ways.pkl",
               "rnodes":"conncomp.pkl",
               "data":"G.pkl",
               "G":"footd.pkl",
               "nodes":"nodes.pkl"}

    def __getattr__(self,attr):
        if attr in self._data:
            return self._data[attr]
        if attr not in self.filenames:
            raise KeyError,attr
        #print attr,self.filenames[attr]
        self._data[attr]=pickle.load(open(self.filenames[attr]))
        return self._data[attr]

data=Data()
