# cidnilib/tests/test_picklefileds.py

import io
import pytest

from cidnilib.picklefileds import PickleFileBasedDataService


@pytest.fixture
def ds(tmp_path):
    test_dir = tmp_path / "cidnilib_pickle_test_store"
    test_dir.mkdir()
    return PickleFileBasedDataService(str(test_dir))


def test_constructor_rejects_missing_path(tmp_path):
    missing_dir = tmp_path / "does_not_exist"

    with pytest.raises(ValueError):
        PickleFileBasedDataService(str(missing_dir))


def test_know_binary_returns_cid_and_stores_data(ds):
    cid, created = ds.know_binary(b"hello")
    assert created is True
    assert ds.known_binary(cid)
    assert ds.recall_binary(cid) == b"hello"


def test_same_data_gets_same_cid(ds):
    cid1, created1 = ds.know_binary(b"same")
    cid2, created2 = ds.know_binary(b"same")

    assert cid1 == cid2
    assert created1 is True
    assert created2 is False
    assert ds.recall_binary(cid1) == b"same"


def test_different_data_gets_different_cids(ds):
    cid1, _ = ds.know_binary(b"one")
    cid2, _ = ds.know_binary(b"two")

    assert cid1 != cid2


def test_list_known_cids(ds):
    cid1, _ = ds.know_binary(b"one")
    cid2, _ = ds.know_binary(b"two")

    assert set(ds.list_known_cids()).issubset({cid1, cid2})


def test_forget_binary_removes_data(ds):
    cid, _ = ds.know_binary(b"temporary")

    assert ds.known_binary(cid)
    
    ds.forget_binary(cid)

    assert not ds.known_binary(cid)
    assert not ds.recall_binary(cid)


def test_recall_unknown_binary_returns_none(ds):
    cid, _ = ds.know_binary(b"known")
    ds.forget_binary(cid)

    assert ds.recall_binary(cid) is None


def test_know_file(ds):
    cid, created = ds.know_file(io.BytesIO(b"file contents"))

    assert created is True
    assert ds.known_binary(cid)
    assert ds.recall_binary(cid) == b"file contents"


def test_known_with_binary_cid(ds):
    cid, _ = ds.know_binary(b"hello")

    assert ds.known(cid)


def test_recall_with_binary_cid(ds):
    cid, _ = ds.know_binary(b"hello")

    assert ds.recall_binary(cid) == b"hello"


def test_recall_stream(ds):
    cid, _ = ds.know_binary(b"streamed")

    stream = ds.recall_stream(cid)

    assert stream.read() == b"streamed"
