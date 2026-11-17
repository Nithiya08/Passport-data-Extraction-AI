"""Unit tests for the in-memory document caching service."""

import time
from app.services.cache_service import InMemoryDocumentCache
from app.schemas import ExtractionResult, PersonalDetails, TravelEvent


def create_sample_result(name: str = "Test User") -> ExtractionResult:
    return ExtractionResult(
        personal_details=PersonalDetails(
            surname="TEST",
            given_names=name,
            full_name=f"{name} TEST",
            passport_number="P12345678",
            issuing_country="India",
            issuing_country_code="IND",
            nationality="Indian"
        ),
        travel_events=[
            TravelEvent(
                event_type="entry_stamp",
                country="France",
                date="2022-04-10"
            )
        ],
        warnings=[]
    )


def test_cache_miss_and_hit():
    cache = InMemoryDocumentCache(max_entries=10, default_ttl_seconds=60)
    buf1 = [b"fake_image_bytes_page_1", b"fake_image_bytes_page_2"]

    doc_hash = cache.compute_hash(buf1)

    # Initial get should be a miss
    assert cache.get(doc_hash) is None
    assert cache.misses == 1
    assert cache.hits == 0

    # Store in cache
    sample = create_sample_result()
    cache.set(doc_hash, sample)

    # Second get should be a hit and flagged as cached
    cached_res = cache.get(doc_hash)
    assert cached_res is not None
    assert cached_res.is_cached is True
    assert cached_res.personal_details.passport_number == "P12345678"
    assert cache.hits == 1


def test_different_documents_different_hashes():
    cache = InMemoryDocumentCache(max_entries=10)
    doc_a = [b"document_a_bytes"]
    doc_b = [b"document_b_bytes"]

    hash_a = cache.compute_hash(doc_a)
    hash_b = cache.compute_hash(doc_b)

    assert hash_a != hash_b

    cache.set(hash_a, create_sample_result("User A"))
    cache.set(hash_b, create_sample_result("User B"))

    res_a = cache.get(hash_a)
    res_b = cache.get(hash_b)

    assert res_a.personal_details.given_names == "User A"
    assert res_b.personal_details.given_names == "User B"


def test_cache_ttl_expiration():
    # Cache with 1 second TTL
    cache = InMemoryDocumentCache(max_entries=10, default_ttl_seconds=1)
    buf = [b"expiring_document"]
    doc_hash = cache.compute_hash(buf)

    cache.set(doc_hash, create_sample_result(), ttl=1)

    # Immediate get succeeds
    assert cache.get(doc_hash) is not None

    # Wait for TTL to elapse
    time.sleep(1.1)

    # Next get should detect expiration and return None
    assert cache.get(doc_hash) is None


def test_cache_lru_eviction():
    # Cache with capacity of 2 entries
    cache = InMemoryDocumentCache(max_entries=2, default_ttl_seconds=60)

    hash_1 = cache.compute_hash([b"doc_1"])
    hash_2 = cache.compute_hash([b"doc_2"])
    hash_3 = cache.compute_hash([b"doc_3"])

    cache.set(hash_1, create_sample_result("Doc 1"))
    time.sleep(0.01)
    cache.set(hash_2, create_sample_result("Doc 2"))
    time.sleep(0.01)

    # Access hash_1 to make hash_2 the least recently used
    _ = cache.get(hash_1)
    time.sleep(0.01)

    # Adding hash_3 should evict hash_2 (least recently accessed)
    cache.set(hash_3, create_sample_result("Doc 3"))

    assert cache.get(hash_1) is not None
    assert cache.get(hash_2) is None  # Evicted
    assert cache.get(hash_3) is not None
    assert cache.stats()["total_cached"] == 2

