import pytest
from api.domain.models import Source, SourceType, SourcePriority, FeedItem, ScoredItem, Tag, Keyword


def test_source_defaults():
    s = Source(url="https://example.com/feed", name="Test", type=SourceType.RSS)
    assert s.active is True
    assert s.priority == SourcePriority.HIGH
    assert s.error_count == 0
    assert s.tag_ids == []


def test_source_web_type():
    s = Source(url="https://blog.example.com", name="Blog", type=SourceType.WEB)
    assert s.type == SourceType.WEB


def test_feed_item_defaults():
    item = FeedItem(source_id=1, url="https://example.com/article", url_hash="abc123", title="Test Artikel")
    assert item.read is False
    assert item.description is None
    assert item.id is None


def test_scored_item_range():
    scored = ScoredItem(item_id=1, score=85, reason="Hohe Relevanz für Tech")
    assert 0 <= scored.score <= 100
    assert scored.keywords_matched == []


def test_tag_defaults():
    tag = Tag(name="Tech")
    assert tag.color == "#00B37E"
    assert tag.id is None


def test_keyword_defaults():
    kw = Keyword(term="OpenAI")
    assert kw.threshold == 60
    assert kw.notify is True
    assert kw.active is True
