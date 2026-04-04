"""Tests for the minimal content seed script."""

from __future__ import annotations

import wave
from pathlib import Path

import pytest

from app.models.card import Card
from app.models.deck import Deck
from app.models.user_card_srs import UserCardSRS
from scripts.seed_minimal_content import (
    MINIMAL_CARD_SPECS,
    MinimalContentSeeder,
    generate_placeholder_wav,
)


class RecordingOSSAdapter:
    """Simple fake OSS adapter that records upload attempts."""

    def __init__(self):
        self.calls: list[tuple[str, str]] = []

    def upload_file_from_path(self, local_path: str, object_path: str) -> bool:
        path = Path(local_path)
        assert path.exists()
        self.calls.append((local_path, object_path))
        return True


@pytest.mark.unit
def test_generate_placeholder_wav_creates_playable_file(tmp_path: Path):
    target = tmp_path / "placeholder.wav"

    generate_placeholder_wav(target, frequency_hz=440)

    assert target.exists()
    with wave.open(str(target), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() > 0


@pytest.mark.unit
def test_minimal_content_seeder_creates_demo_content(test_db, tmp_path: Path):
    fake_oss = RecordingOSSAdapter()
    seeder = MinimalContentSeeder(test_db, oss_adapter=fake_oss, temp_root=tmp_path)

    report = seeder.seed(if_empty=True)

    assert report.seeded is True
    assert report.card_count == len(MINIMAL_CARD_SPECS)
    assert test_db.query(Deck).filter(Deck.type == "source").count() == 1
    assert test_db.query(Deck).filter(Deck.type == "unit").count() == 1
    assert test_db.query(Deck).filter(Deck.type == "lesson").count() == 1
    assert test_db.query(Card).count() == len(MINIMAL_CARD_SPECS)
    assert test_db.query(UserCardSRS).count() == len(MINIMAL_CARD_SPECS)
    assert len(fake_oss.calls) == len(MINIMAL_CARD_SPECS)

    cards = test_db.query(Card).order_by(Card.card_index).all()
    assert [card.audio_path for card in cards] == [
        spec.audio_object_path for spec in MINIMAL_CARD_SPECS
    ]


@pytest.mark.unit
def test_minimal_content_seeder_is_idempotent_when_content_exists(test_db, tmp_path: Path):
    first_oss = RecordingOSSAdapter()
    seeder = MinimalContentSeeder(test_db, oss_adapter=first_oss, temp_root=tmp_path)
    first_report = seeder.seed(if_empty=True)

    second_oss = RecordingOSSAdapter()
    second_report = MinimalContentSeeder(
        test_db,
        oss_adapter=second_oss,
        temp_root=tmp_path,
    ).seed(if_empty=True)

    assert first_report.seeded is True
    assert second_report.seeded is False
    assert second_report.reason == "business content already exists"
    assert test_db.query(Card).count() == len(MINIMAL_CARD_SPECS)
    assert len(second_oss.calls) == 0
