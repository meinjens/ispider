from datetime import datetime
from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey, Integer,
    String, Text, Table
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class SourceTypeORM(str, enum.Enum):
    rss = "rss"
    web = "web"


class SourcePriorityORM(str, enum.Enum):
    high = "high"
    low = "low"


source_tag_table = Table(
    "source_tags",
    Base.metadata,
    Column("source_id", Integer, ForeignKey("sources.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class SourceORM(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    type = Column(Enum(SourceTypeORM), nullable=False, default=SourceTypeORM.rss)
    active = Column(Boolean, default=True, nullable=False)
    priority = Column(Enum(SourcePriorityORM), default=SourcePriorityORM.high, nullable=False)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_fetched_at = Column(DateTime, nullable=True)

    tags = relationship("TagORM", secondary=source_tag_table, back_populates="sources")
    items = relationship("FeedItemORM", back_populates="source", cascade="all, delete-orphan")


class FeedItemORM(Base):
    __tablename__ = "feed_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    url = Column(String, nullable=False)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    raw_content = Column(Text, nullable=True)
    pub_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    read = Column(Boolean, default=False)

    source = relationship("SourceORM", back_populates="items")
    score = relationship("ScoredItemORM", back_populates="item", uselist=False, cascade="all, delete-orphan")


class ScoredItemORM(Base):
    __tablename__ = "scored_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey("feed_items.id", ondelete="CASCADE"), nullable=False, unique=True)
    score = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    keywords_matched = Column(Text, default="")   # JSON-serialisierte Liste
    notified_at = Column(DateTime, nullable=True)
    scored_at = Column(DateTime, default=datetime.utcnow)

    item = relationship("FeedItemORM", back_populates="score")


class TagORM(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    color = Column(String, default="#00B37E")

    sources = relationship("SourceORM", secondary=source_tag_table, back_populates="tags")


class KeywordORM(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String, nullable=False, unique=True)
    threshold = Column(Integer, default=60)
    notify = Column(Boolean, default=True)
    active = Column(Boolean, default=True)


class PushSubscriptionORM(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String, nullable=False, unique=True)
    p256dh = Column(String, nullable=False)
    auth = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
