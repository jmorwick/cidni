"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

from .main import DataService


class SplitterDataService(DataService):
    """joins two data services together, using the first for small data and the latter for large data (bigger than size_limit)"""
    def __init__(self,
                 ds1:DataService,
                 ds2:DataService,
                 size_limit: int = 256):  
        
        super().__init__(ds1.encode, ds1.decode, ds1.hasher)
        self.ds1 = ds1
        self.ds2 = ds2
        self.size_limit = size_limit


    def know_binary(self, data:bytes):
        if len(data) < self.size_limit:
            return self.ds1.know_binary(data)
        else:
            return self.ds2.know_binary(data)

    def known_binary(self, id:bytes) -> bool:
        return self.ds1.known_binary(id) or self.ds2.known_binary(id)

    def recall_binary(self, id:bytes) -> bytes:
        return self.ds1.recall_binary(id) or self.ds2.recall_binary(id)

    def forget_binary(self, id:bytes) -> bytes:
        return self.ds1.forget_binary(id) or self.ds2.forget_binary(id)

    def list_known_cids(self) -> Iterator[bytes]:
        yield from self.ds1.list_known_cids()
        yield from self.ds2.list_known_cids()
        
