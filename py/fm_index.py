from os import path
from ctypes import *

class FMIndex:
    
    def __init__(self, fn, libfm_index_name="libfm_index.so"):
        fmi_path = fn if fn.endswith(".fmi") else "%s.fmi" % fn
        self.libfm = CDLL(libfm_index_name)
        if path.exists(fmi_path):
            self.load(fn)
        elif path.exists(fn):
            self.build(fn)
        else:
            raise IOError("Specify a path to build or load index from; %s and %s don't exist" % (fmi_path, fn))
    
    def build(self, fn, outfile=None, buckets1=16, buckets2=512, freq=64):
        outfile = outfile if outfile else fn
        self.libfm.fm_build_index(fn.encode('utf-8'), outfile.encode("utf-8"), buckets1, buckets2, freq)
        self.load(outfile)
    
    def load(self, fn):
        self._index = c_void_p()
        if fn.endswith(".fmi"):
            fn = fn[:-4]
        err = self.libfm.load_index(fn.encode("utf-8"), byref(self._index))
        if err:
            raise Error("Error loading index: %d" % err)
    
    def count(self, pattern):
        num_occs = c_int()
        err = self.libfm.count(self._index, pattern.encode("utf-8"), len(pattern), byref(num_occs))
        if err:
            raise Error("Error locating %s: %d" % (pattern, err))
        return num_occs.value

    def locate(self, pattern):
        occs = pointer(c_int())
        num_occs = c_int()
        err = self.libfm.locate(self._index, pattern.encode("utf-8"), len(pattern), byref(occs), byref(num_occs))
        if err:
            raise Error("Error locating %s: %d" % (pattern, err))
        ret = []
        for i in range(num_occs.value):
            ret.append(occs[i])
        return ret, num_occs.value
    
    def display(self, pattern, num_chars):
        text = c_char_p()
        lengths = pointer(c_int())
        num_occs = c_int()
        err = self.libfm.display(
            self._index, 
            pattern.encode("utf-8"), 
            len(pattern), 
            num_chars, 
            byref(num_occs),
            byref(text),
            byref(lengths)
        )
        if err:
            raise Error("Error locating %s: %d" % (pattern, err))
        texts = []
        idx = 0
        ls = []
        for i in range(num_occs.value):
            texts.append(text.value[idx:idx+lengths[i]])
            ls.append(lengths[i])
            idx += lengths[i]
        return num_occs.value, texts, ls
    
    def extract(self, pos, num):
        text = c_char_p()
        read = c_int()
        err = self.libfm.extract(self._index, pos, pos + num - 1, byref(text), byref(read))
        if err:
            raise Error("Error extracting from index: %d" % err)
        return text.value[:num]
