"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from abc import abstractmethod
from collections.abc import Callable
from typing import BinaryIO, Iterator
from hashlib import sha256
from typing import Protocol, runtime_checkable
from multihash import to_b58_string, from_b58_string, encode
from io import BytesIO
from collections import defaultdict
import json

@runtime_checkable
class HashAlgorithm(Protocol):
    def update(self, data: bytes) -> None: ...
    def digest(self) -> bytes: ...

hashers = {
    12: sha256
}

class MultiHashEncoder(HashAlgorithm):

    def __init__(self, code:int=12):
        self.hasher = hashers[code]()
        self.code = code

    def update(self, data:bytes):
        self.hasher.update(data)

    def digest(self):
        return encode(self.hasher.digest(), self.code)
    
class DataService:

    def __init__(self, 
                 encoder: Callable[[bytes],str] = to_b58_string, 
                 decoder: Callable[[str],bytes] = from_b58_string, 
                 hasher: Callable[[],HashAlgorithm] = MultiHashEncoder,
                 text_encoding: str = 'utf8'): 
        self.encode = encoder
        self.decode = decoder
        self.hasher = hasher
        self.text_encoding = text_encoding
        
    #TODO finish/test/integrate
    def cid(self, data:bytes|str) -> bytes:
        m = self.hasher()
        m.update(data)
        id = self.encode(m.digest())
        return id


    @abstractmethod
    def know_binary(self, data:bytes) -> tuple[bytes, bool]:
        """remember given data for future retrieval"""
        pass

    @abstractmethod
    def known_binary(self, id:bytes) -> bool:
        """determine if value is available for given id"""
        pass

    @abstractmethod
    def recall_binary(self, id:bytes) -> bytes:
        """retrieve data associated with id"""
        pass

    @abstractmethod
    def forget_binary(self, id:bytes) -> bytes:
        """forget data associated with id"""
        pass

    @abstractmethod
    def list_known_cids(self) -> Iterator[bytes]:
        """list all known cids"""
        pass
        
    def know_file(self, fp:BinaryIO) -> tuple[bytes, bool]: 
        """remember given data for future retrieval
        
            returns the cid of the data along with a boolean representing whether 
            the data was unknown to the data service"""
        return self.know_binary(fp.read())

    def know(self, data:str|bytes) -> tuple[bytes, bool]: 
        """remember given data for future retrieval
        
            data is either a string (not string-encoded binary data) or raw binary data
        
            returns the cid of the data along with a boolean representing whether 
            the data was unknown to the data service
        """
        return self.know_binary(bytes(data, self.text_encoding)) if type(data) == str else self.know_binary(data)

    def recall(self, id:bytes|str) -> bytes:
        """retrieve data associated with id
        
            id is either binary hash or binary hash encoded as a string (using self.encode)
        
        """
        return self.recall_binary(self.decode(id)) if type(id) == str else self.recall_binary(id)

    def recall_text(self, id:bytes|str) -> str:
        """retrieve data associated with id as a string
        
            id is either binary hash or binary hash encoded as a string (using self.encode)
            
            returns data as a string (decoded from binary storage)
            """
        return self.recall(id).decode(self.text_encoding)

    def recall_stream(self, id:bytes|str) -> BinaryIO:
        """retrieve data associated with id
        
            id is either binary hash or binary hash encoded as a string (using self.encode)
            
        """
        id = id if type(id) == bytes else self.decode(id)
        return BytesIO(self.recall_binary(id))
        
    def forget(self, id:bytes|str) -> bytes:
        """forget data associated with id
        
            id is either binary hash or binary hash encoded as a string (using self.encode)
            
        """
        return self.forget_binary(id) if type(id) == bytes else self.forget_binary(self.decode(id))

    def known(self, id:bytes|str) -> bool:
        """determine if value is available for given id
        
            id is either binary hash or binary hash encoded as a string (using self.encode)
            
        """
        return self.known_binary(id) if type(id) == bytes else self.known_binary(self.decode(id))




class InMemoryDataService(DataService):
    def __init__(self,
                 encoder: Callable[[bytes],str] = to_b58_string, 
                 decoder: Callable[[str],bytes] = from_b58_string, 
                 hasher: Callable[[],HashAlgorithm] = MultiHashEncoder):  

        
        super().__init__(encoder, decoder, hasher)
        self.db = dict()

    def know_binary(self, data:bytes):
        m = self.hasher()
        m.update(data)
        id = m.digest()
        self.db[id] = data
        return id, True

    def known_binary(self, id:bytes):
        return id in self.db

    def recall_binary(self, id:bytes):
        try: return self.db[id]
        except: return None

    def forget_binary(self, id:bytes):
        try: del self.db[id]
        except: return None

    def list_known_cids(self) -> Iterator[bytes]:
        return self.db.keys()




class KnowledgeService:

    def __init__(self, 
                 ds: DataService = InMemoryDataService()):   # data  holding serialized triples
        self.ds = ds

    #TODO finish/test/integrate
    def encode(self, subject: str, property: str, value: str) -> bytes:
        """Associate a string annotation with a string subject."""
        triple_text = json.dumps([subject, property, value])
        return self.ds.know(triple_text)

    def believe(self, subject: str, property: str, value: str) -> tuple[bytes, bool]:
        """Associate a string annotation with a string subject."""
        triple_text = json.dumps([subject, property, value])
        return self.ds.know(triple_text)

    @abstractmethod
    def inquire(self, subject:str|None, property:str|None, value:str|None) -> Iterator[tuple[str, str, str]]:
        """retrieve annotations associated with id"""
        pass
        
class InMemoryKnowledgeService(KnowledgeService):
    def __init__(self, ds: DataService = InMemoryDataService()):    # data service holding serialized triples 
        self.ds = ds
        self.subj_to_prop_to_vals = defaultdict(lambda: defaultdict(set))
        self.prop_to_val_to_subjs = defaultdict(lambda: defaultdict(set))

        for cid in ds.list_known_cids():
            
            try:
                data = ds.recall_binary(cid)
                text = data.decode("utf-8")
                triple = json.loads(text)
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError):
                continue

            if (
                isinstance(triple, list)
                and len(triple) == 3
                and all(isinstance(x, str) for x in triple)
            ):
                subject, property, value = triple
                self._index(subject, property, value)

    def _index(self, subject: str, property: str, value: str) -> None:
        self.subj_to_prop_to_vals[subject][property].add(value)
        self.prop_to_val_to_subjs[property][value].add(subject)

    def inquire(
        self,
        subject: str | None = None,
        property: str | None = None,
        value: str | None = None,
    ) -> Iterator[tuple[str, str, str]]:
        """Retrieve matching string triples."""
        if subject is not None:
            for prop in ([property] if property is not None else self.subj_to_prop_to_vals[subject].keys()):
                vals = self.subj_to_prop_to_vals[subject][prop]
                for val in vals:
                    if value is None or value == val:
                        yield subject, prop, val

        elif property is not None:
            for val in ([value] if value is not None else self.prop_to_val_to_subjs[property].keys()):
                for subj in self.prop_to_val_to_subjs[property][val]:
                    yield subj, property, val

        else:
            for subj, prop_to_vals in self.subj_to_prop_to_vals.items():
                for prop, vals in prop_to_vals.items():
                    for val in vals:
                        if value is None or value == val:
                            yield subj, prop, val
