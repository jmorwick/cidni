"""
Copyright © 2025 Joseph Kendall-Morwick

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import json
from collections import defaultdict
from typing import Iterator

from .main import DataService, KnowledgeService


class InMemoryKnowledgeService(KnowledgeService):
    def __init__(self, ds: DataService):
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

    def believe(self, subject: str, property: str, value: str) -> tuple[bytes, bool]:
        """Associate a string annotation with a string subject."""
        self._index(subject, property, value)
        triple_text = json.dumps([subject, property, value])
        return self.ds.know(triple_text)

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
