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
import os
import sys
from os.path import exists
from multihash import to_b58_string, from_b58_string


class FileBasedDataService(DataService):
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

    def resolve_path(self, id:str):
        """find file on the path that matches the id if it exists"""
        subdir = ''
        for i in range(self.levels):
            subdir += id[-i-1] + '/'
            if not exists(self.path+'/'+subdir):
                os.mkdir(self.path+'/'+subdir)
        path = self.path+'/'+subdir+id+'.bin' 
        return path

    def file_store(self, id:str, data:bytes):
        """create new file to store data in"""
        path = self.resolve_path(id)
        if not exists(path):
            fp = open(path, 'wb')
            fp.write(data)
            fp.close()





    def know_binary(self, data:bytes):
        m = self.hasher()
        m.update(data)
        id = self.encode(m.digest())
        if not exists(self.resolve_path(id)):
            self.file_store(id, data)
            return self.decode(id), True
        else:
            return self.decode(id), False

    def known_binary(self, id:bytes):
        print(self.resolve_path(self.encode(id)))
        return exists(self.resolve_path(self.encode(id)))
        
    def recall_binary(self, id:bytes):
        """retrieve data associated with name"""
        path = self.resolve_path(self.encode(id))
        if exists(path):
            fp = open(path, 'rb')
            data = fp.read()
            fp.close()
            return data

    def forget_binary(self, id:bytes):
        """forget data associated with name"""
        path = self.resolve_path(self.encode(id))
        if exists(path):
            os.remove(path)

    def list_known_cids(self) -> Iterator[str]:
        """Yield all known CIDs"""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.endswith('.bin'):
                    yield self.decode(file[:-4])  # Strip ".bin" to get the CID



    def know_file(self, fp:BinaryIO):
        m = self.hasher()
        while True:
            data = fp.read(104857600)
            if not data:
                break
            m.update(data)
            print(".", end="", flush=True, file=sys.stderr)
        digest = m.digest()
        id = self.encode(digest)
        path = self.resolve_path(id)
        if not exists(path):
            fp.seek(0)
            fpo = open(path, 'wb')
            while True:
                data = fp.read(104857600)
                if not data:
                    break
                fpo.write(data)
                print(".", end="", flush=True, file=sys.stderr)
            fpo.close()
            return self.decode(id), True
        else:
            return self.decode(id), False
            

    def recall_stream(self, id:bytes|str):
        """retrieve data associated with name"""
        if type(id) == bytes: id = self.encode(id)
        path = self.resolve_path(id)

        if exists(path):
            fp = open(path, 'rb')
            return fp

