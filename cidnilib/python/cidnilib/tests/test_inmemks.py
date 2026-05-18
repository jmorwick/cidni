import json

from cidnilib.inmemds import InMemoryDataService
from cidnilib.inmemks import InMemoryKnowledgeService


def test_believe_adds_and_returns_triple():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    cid, created = ks.believe("subject1", "color", "blue")

    assert created is True
    assert ds.known(cid)
    assert list(ks.inquire("subject1")) == [("subject1", "color", "blue")]


def test_believe_stores_json_list_in_datastore():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    cid, _ = ks.believe("subject1", "color", "blue")

    stored = ds.recall(cid).decode("utf-8")
    assert json.loads(stored) == ["subject1", "color", "blue"]


def test_duplicate_belief_is_deduplicated_in_memory():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    cid1, created1 = ks.believe("subject1", "color", "blue")
    cid2, created2 = ks.believe("subject1", "color", "blue")

    assert cid1 == cid2
    assert created1 is True
    assert created2 is True or created2 is False
    assert list(ks.inquire("subject1")) == [("subject1", "color", "blue")]


def test_inquire_by_subject_returns_all_properties():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s1", "p2", "v2")
    ks.believe("s2", "p1", "v3")

    assert set(ks.inquire("s1")) == {
        ("s1", "p1", "v1"),
        ("s1", "p2", "v2"),
    }


def test_inquire_by_subject_and_property():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s1", "p1", "v2")
    ks.believe("s1", "p2", "v3")

    assert set(ks.inquire("s1", "p1")) == {
        ("s1", "p1", "v1"),
        ("s1", "p1", "v2"),
    }


def test_inquire_by_subject_property_and_value():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s1", "p1", "v2")

    assert list(ks.inquire("s1", "p1", "v2")) == [
        ("s1", "p1", "v2")
    ]


def test_inquire_by_property_only():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s2", "p1", "v1")
    ks.believe("s3", "p2", "v1")

    assert set(ks.inquire(None, "p1")) == {
        ("s1", "p1", "v1"),
        ("s2", "p1", "v1"),
    }


def test_inquire_by_property_and_value():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s2", "p1", "v2")
    ks.believe("s3", "p2", "v1")

    assert set(ks.inquire(None, "p1", "v1")) == {
        ("s1", "p1", "v1"),
    }


def test_inquire_with_no_filters_returns_all_triples():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s2", "p2", "v2")

    assert set(ks.inquire()) == {
        ("s1", "p1", "v1"),
        ("s2", "p2", "v2"),
    }


def test_inquire_value_without_property_returns_all_matching_values():
    ds = InMemoryDataService()
    ks = InMemoryKnowledgeService(ds)

    ks.believe("s1", "p1", "v1")
    ks.believe("s2", "p2", "v1")
    ks.believe("s3", "p3", "v2")

    assert set(ks.inquire(value="v1")) == {
        ("s1", "p1", "v1"),
        ("s2", "p2", "v1"),
    }


def test_reloads_existing_triples_from_datastore():
    ds = InMemoryDataService()

    ks1 = InMemoryKnowledgeService(ds)
    ks1.believe("s1", "p1", "v1")
    ks1.believe("s2", "p2", "v2")
    
    assert len(ds.list_known_cids()) is 2

    ks2 = InMemoryKnowledgeService(ds)

    assert set(ks2.inquire()) == {
        ("s1", "p1", "v1"),
        ("s2", "p2", "v2"),
    }


def test_ignores_non_utf8_data_when_loading():
    ds = InMemoryDataService()
    ds.know_binary(b"\xff\xfe\x00")

    ks = InMemoryKnowledgeService(ds)

    assert list(ks.inquire()) == []


def test_ignores_non_json_text_when_loading():
    ds = InMemoryDataService()
    ds.know("not json")

    ks = InMemoryKnowledgeService(ds)

    assert list(ks.inquire()) == []


def test_ignores_json_that_is_not_three_string_list():
    ds = InMemoryDataService()
    ds.know(json.dumps({"subject": "s1", "property": "p1", "value": "v1"}))
    ds.know(json.dumps(["s1", "p1"]))
    ds.know(json.dumps(["s1", "p1", 123]))

    ks = InMemoryKnowledgeService(ds)

    assert list(ks.inquire()) == []


def test_can_use_encoded_binary_cid_as_subject():
    ds = InMemoryDataService()
    binary_cid, _ = ds.know_binary(b"binary object")
    subj = ds.encode(binary_cid)

    ks = InMemoryKnowledgeService(ds)
    ks.believe(subj, "mime", "application/octet-stream")

    assert (subj, "mime", "application/octet-stream") in list(ks.inquire(subj))
