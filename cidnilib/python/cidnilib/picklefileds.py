"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from .main import DataService, KnowledgeService, HashAlgorithm, MultiHashEncoder
from collections.abc import Callable
from typing import BinaryIO, Iterator
from io import BytesIO
from pickledb import PickleDB
import os
import sys
from os.path import exists
from multihash import to_b58_string, from_b58_string


class PickleFileBasedDataService(DataService):
    def __init__(self,
                 path: str,
                 encoder: Callable[[bytes],str] = to_b58_string, 
                 decoder: Callable[[str],bytes] = from_b58_string, 
                 hasher: Callable[[],HashAlgorithm] = MultiHashEncoder,
                 levels: int = 2):  
        if not os.path.exists(path):
            raise ValueError('Path {path} does not exist.'.format(path=path))
            
        super().__init__(encoder, decoder, hasher)
        self.path = path
        self.levels = levels
        self.dbcache = dict()
        self._closed = False
        self.dirty_dbs = set()
        
        
    def resolve_db(self, id:str) -> PickleDB:
        """find pickledb on the path that matches the name and generate if it doesn't exist"""
        if self.levels == 0:
            if self.dbcache:
              return self.dbcache['']
            self.dbcache[''] = PickleDB(self.path+'/'+'pickle.db') 
            self.dbcache[''].load()
            return self.dbcache['']
        
        if id[-self.levels-1:-1] in self.dbcache:
            return self.dbcache[id[-self.levels-1:-1]]
        subdir = ''
        for i in range(self.levels):
            subdir += id[-i-1] + '/'
            if not exists(self.path+'/'+subdir):
                os.mkdir(self.path+'/'+subdir)
        db = PickleDB(self.path+'/'+subdir+'pickle.db') 
        db.load()
        self.dbcache[id[-self.levels-1:-1]] = db
        return db

    def know_binary(self, data:bytes):
        m = self.hasher()
        m.update(data)
        id = m.digest()
        
        db = self.resolve_db(self.encode(id))
        if not db.get(self.encode(id)):
            db.set(self.encode(id), self.encode(data))
            self.dirty_dbs.add(db)
            return id, True
        else:
            return id, False

    def known_binary(self, id:bytes) -> bool:
        """determine if value is available for given id"""
        db = self.resolve_db(self.encode(id))
        return db.get(self.encode(id))

    def recall_binary(self, id:bytes):
        """retrieve data associated with name"""
        db = self.resolve_db(self.encode(id))
        data = db.get(self.encode(id))
        if not data: return None
        return self.decode(data)

    def forget_binary(self, id:bytes) -> bytes:
        """forget data associated with id"""
        db = self.resolve_db(self.encode(id))
        db.remove(self.encode(id))
        self.dirty_dbs.add(db)

    def list_known_cids(self) -> Iterator[bytes]:
        """Yield all known CIDs"""
        if self.levels == 0:
          db = self.resolve_db('')
          yield from map(self.decode, db.all())  
          
        else:
            self.flush()
            for root, dirs, files in os.walk(self.path):
                if 'pickle.db' in files:
                    db_path = os.path.join(root, 'pickle.db')
                    db = PickleDB(db_path)
                    db.load()
                    yield from map(self.decode, db.all())
                

    def flush(self):
        for db in self.dirty_dbs():
            db.save()
        self.dirty_dbs = set()

    def close(self):
        if getattr(self, "_closed", False):
            return
        self.flush()
        self._closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
