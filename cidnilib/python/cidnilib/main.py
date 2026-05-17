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
                 hasher: Callable[[],HashAlgorithm] = MultiHashEncoder): 
        self.encode = encoder
        self.decode = decoder
        self.hasher = hasher


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
        """remember given data for future retrieval"""
        return self.know_binary(fp.read())

    def know(self, data:str|bytes) -> tuple[bytes, bool]: 
        """remember given data for future retrieval"""
        return self.know_binary(bytes(data, 'utf8')) if type(data) == str else self.know_binary(data)

    def recall(self, id:bytes|str) -> bytes:
        """retrieve data associated with id"""
        return self.recall_binary(self.decode(id)) if type(id) == str else self.recall_binary(id)

    def recall_text(self, id:bytes|str) -> bytes:
        """retrieve data associated with id"""
        return str(self.recall_binary(self.decode(id))) if type(id) == str else str(self.recall_binary(id))

    def recall_stream(self, id:bytes|str) -> BinaryIO:
        """retrieve data associated with id"""
        id = id if type(id) == bytes else self.decode(id)
        return BytesIO(self.recall_binary(id))
        
    def forget(self, id:bytes|str) -> bytes:
        """forget data associated with id"""
        return self.forget_binary(id) if type(id) == bytes else self.forget_binary(self.decode(id))

    def known(self, id:bytes|str) -> bool:
        """determine if value is available for given id"""
        return self.known_binary(id) if type(id) == bytes else self.known_binary(self.decode(id))


class KnowledgeService:

    @abstractmethod
    def believe(self, subject: str, property: str, value: str) -> tuple[bytes, bool]:
        """associate annotation with data"""
        pass

    @abstractmethod
    def inquire(self, subject:str|None, property:str|None, value:str|None) -> Iterator[tuple[str, str, str]]:
        """retrieve annotations associated with id"""
        pass
