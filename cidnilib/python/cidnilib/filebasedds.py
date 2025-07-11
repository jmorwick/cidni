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
import sqlite3
from os.path import exists
from multihash import to_b58_string, from_b58_string

init_sql = """CREATE TABLE kb (
    cid     BLOB PRIMARY KEY,
    subject BLOB NOT NULL,
    property TEXT NOT NULL,
    value   TEXT NOT NULL
);

CREATE INDEX idx_subject ON kb(subject);

CREATE INDEX idx_subject_property ON kb(subject, property);

CREATE INDEX idx_property_value ON kb(property, value);
"""
    



each_sql = """
-- Enable Write-Ahead Logging (WAL)
PRAGMA journal_mode=WAL;

-- Increase cache size
  -- 50MB cache

-- Disable synchronous writes for faster performance


-- Enable memory-mapped I/O

"""

class FileBasedDataService(DataService,KnowledgeService):
    def __init__(self,
                 path: str,
                 encoder: Callable[[bytes],str] = to_b58_string, 
                 decoder: Callable[[str],bytes] = from_b58_string, 
                 hasher: Callable[[],HashAlgorithm] = MultiHashEncoder,
                 size_limit: int = 256, 
                 levels: int = 2):  
        if not os.path.exists(path):
            raise ValueError('Path {path} does not exist.'.format(path=path))
        if not os.path.exists(path+'/fbds-kb.db'):
            self.dbcon = sqlite3.connect(path+'/fbds-kb.db')
            cursor = self.dbcon.cursor()
            cursor.executescript(init_sql)
            self.dbcon.commit()
        else:
            self.dbcon = sqlite3.connect(path+'/fbds-kb.db')
            
        super().__init__(encoder, decoder, hasher)
        self.path = path
        self.size_limit = size_limit
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

    def resolve_db(self, id:str) -> PickleDB:
        """find pickledb on the path that matches the name and generate if it doesn't exist"""
        subdir = ''
        for i in range(self.levels):
            subdir += id[-i-1] + '/'
            if not exists(self.path+'/'+subdir):
                os.mkdir(self.path+'/'+subdir)
        return PickleDB(self.path+'/'+subdir+'pickle.db')  

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
            return id, True
        else:
            return id, False

    def known(self, id:str):
        db = self.resolve_db(id)
        return db[id] or exists(self.resolve_path(id))

    def know(self, data:bytes):
        m = self.hasher()
        m.update(data)
        id = self.encode(m.digest())
        if len(data) < self.size_limit:
            # store in pickledb
            db = self.resolve_db(id)
            if not db.get(id):
                db[id] = self.encode(data)
                db.save()
                return id, True
            else:
                return id, False
        else:
            # store in file
            if not exists(self.resolve_path(id)):
                self.file_store(id, data)
                return id, True
            else:
                return id, False

    def recall(self, id:str):
        """retrieve data associated with name"""
        # TODO: handle collisions
        path = self.resolve_path(id)
        if exists(path):
            fp = open(path, 'rb')
            data = fp.read()
            fp.close()
            return data
        else:
            db = self.resolve_db(id)
            data = db[id]
            if not data: return None
            return self.decode(data)

    def recall_stream(self, id:str):
        """retrieve data associated with name"""
        # TODO: handle collisions
        path = self.resolve_path(id)
        if exists(path):
            fp = open(path, 'rb')
            return fp
        else:
            db = self.resolve_db(id)
            return BytesIO(self.decode(db[id]))

    def recall_binary(self, id:bytes):
        return self.recall(self.encode(id))

    def forget(self, id:str):
        """forget data associated with name"""
        path = self.resolve_path(id)
        if exists(path):
            os.remove(path)
        else:
            db = self.resolve_db(id)
            del db[id]

    def forget_binary(self, id:bytes):
        return self.recall(self.encode(id))

    def list_known_cids(self) -> Iterator[str]:
        """Yield all known CIDs"""
        for root, dirs, files in os.walk(self.path):
            for file in files:
                if file.endswith('.bin'):
                    yield file[:-4]  # Strip ".bin" to get the CID

            if 'pickle.db' in files:
                db_path = os.path.join(root, 'pickle.db')
                db = PickleDB(db_path)
                yield from db.getall()


    def believe(self, subject:bytes, property:str, value:str) -> tuple[bytes, bool]:
        """associate annotation with data"""
        cursor = self.dbcon.cursor()

        tripletxt = self.encode(subject) + "," + property + "," + value
        
        m = self.hasher()
        m.update(bytes(tripletxt, 'utf8'))
        cid = m.digest()

        cursor.execute("SELECT cid FROM kb WHERE cid = ?", (cid,))
        if cursor.fetchone():
            return cid, False  
        
        cursor.execute("INSERT INTO kb (cid, subject, property, value) VALUES (?, ?, ?, ?)", (cid, subject, property, value))
        
        self.dbcon.commit()
        return cid, True

    def inquire(self, subject:bytes|None, property:str|None = None, value:str|None=None) -> Iterator[tuple[bytes, bytes, str, str]]:
        """retrieve annotations associated with id"""
        cursor = self.dbcon.cursor()
        query = "SELECT cid, subject, property, value FROM kb WHERE "
        params = ()

        if subject is not None:
            query += " subject = ?"
            params += (subject,)
        if value is not None:
            query += (" AND " if subject is not None else "") + " value = ?"
            params += (value,)
        if property is not None:
            query += " AND property = ?"
            params += (property,)

        cursor.execute(query, params)
        for row in cursor.fetchall():
            yield (row[0], row[1], row[2], row[3])
