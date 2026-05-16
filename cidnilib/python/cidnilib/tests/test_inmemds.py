import io
import pytest

from cidnilib.inmemds import InMemoryDataService


@pytest.fixture
def ds():
    return InMemoryDataService()


def test_know_binary_returns_cid_and_stores_data(ds):
    cid, created = ds.know_binary(b"hello")

    assert created is True
    assert ds.known_binary(cid)
    assert ds.recall_binary(cid) == b"hello"


def test_same_data_gets_same_cid(ds):
    cid1, _ = ds.know_binary(b"same")
    cid2, _ = ds.know_binary(b"same")

    assert cid1 == cid2
    assert ds.recall_binary(cid1) == b"same"


def test_different_data_gets_different_cids(ds):
    cid1, _ = ds.know_binary(b"one")
    cid2, _ = ds.know_binary(b"two")

    assert cid1 != cid2


def test_list_known_cids(ds):
    cid1, _ = ds.know_binary(b"one")
    cid2, _ = ds.know_binary(b"two")

    assert set(ds.list_known_cids()) == {cid1, cid2}


def test_forget_binary_removes_data(ds):
    cid, _ = ds.know_binary(b"temporary")

    ds.forget_binary(cid)

    assert not ds.known_binary(cid)
    with pytest.raises(KeyError):
        ds.recall_binary(cid)


def test_recall_unknown_binary_raises_keyerror(ds):
    with pytest.raises(KeyError):
        ds.recall_binary("not-a-real-cid")



def test_know_file(ds):
    cid, created = ds.know_file(io.BytesIO(b"file contents"))

    assert created is True
    assert ds.recall_binary(cid) == b"file contents"



def test_known_with_binary_cid(ds):
    cid, _ = ds.know_binary(b"hello")

    assert ds.known(cid) is True



def test_recall_with_text_cid(ds):
    cid, _ = ds.know_binary(b"hello")

    assert ds.recall_binary(cid) == b"hello"



def test_recall_stream(ds):
    cid, _ = ds.know_binary(b"streamed")

    stream = ds.recall_stream(cid)

    assert stream.read() == b"streamed"
