"""Seed a minimal demo lesson for Docker and local empty-database setups."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import tempfile
import wave
from dataclasses import asdict, dataclass
from pathlib import Path

from sqlalchemy.orm import Session

# Allow running the script as `python scripts/seed_minimal_content.py`.
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adapters.oss_adapter import OSSAdapter
from app.database import SessionLocal
from app.models.card import Card
from app.models.deck import Deck
from app.models.user_card_srs import UserCardSRS
from app.repositories.card_repo import CardRepository
from app.repositories.deck_repo import DeckRepository
from app.repositories.srs_repo import SRSRepository
from app.utils.timezone import app_now

SEED_SOURCE_TITLE = "LanGear Demo Course"
SEED_UNIT_TITLE = "Unit 1"
SEED_LESSON_TITLE = "Lesson 1: Docker Demo"
SEED_AUDIO_PREFIX = "lessons/bootstrap/unit-01/lesson-01"


@dataclass(frozen=True)
class SeedCardSpec:
    card_index: int
    front_text: str
    back_text: str
    audio_object_path: str
    frequency_hz: int


MINIMAL_CARD_SPECS = [
    SeedCardSpec(
        card_index=0,
        front_text="Welcome to your first LanGear practice sentence.",
        back_text="欢迎来到你的第一句 LanGear 练习。",
        audio_object_path=f"{SEED_AUDIO_PREFIX}/card-01.wav",
        frequency_hz=440,
    ),
    SeedCardSpec(
        card_index=1,
        front_text="Listen to the reference audio and retell it in English.",
        back_text="先听参考音频，再用英文复述。",
        audio_object_path=f"{SEED_AUDIO_PREFIX}/card-02.wav",
        frequency_hz=554,
    ),
    SeedCardSpec(
        card_index=2,
        front_text="Your recording will be uploaded and reviewed asynchronously.",
        back_text="你的录音会被上传并异步评测。",
        audio_object_path=f"{SEED_AUDIO_PREFIX}/card-03.wav",
        frequency_hz=659,
    ),
    SeedCardSpec(
        card_index=3,
        front_text="This placeholder lesson is for technical validation only.",
        back_text="这个占位课程仅用于技术验收。",
        audio_object_path=f"{SEED_AUDIO_PREFIX}/card-04.wav",
        frequency_hz=784,
    ),
]


@dataclass
class SeedReport:
    seeded: bool
    reason: str
    source_count: int
    card_count: int
    audio_object_paths: list[str]


def generate_placeholder_wav(
    target_path: Path,
    frequency_hz: int,
    duration_seconds: float = 0.55,
    sample_rate: int = 16_000,
) -> Path:
    """Generate a short mono WAV tone that can be played in the browser."""
    frame_count = max(1, int(duration_seconds * sample_rate))
    amplitude = 0.25

    with wave.open(str(target_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        for index in range(frame_count):
            sample = amplitude * math.sin(2 * math.pi * frequency_hz * index / sample_rate)
            frames.extend(struct.pack("<h", int(sample * 32767)))
        wav_file.writeframes(bytes(frames))

    return target_path


class MinimalContentSeeder:
    """Create a minimal lesson tree plus placeholder reference audio."""

    def __init__(
        self,
        db: Session,
        oss_adapter: OSSAdapter | None = None,
        temp_root: Path | None = None,
    ):
        self.db = db
        self.oss_adapter = oss_adapter or OSSAdapter()
        self.deck_repo = DeckRepository(db)
        self.card_repo = CardRepository(db)
        self.srs_repo = SRSRepository(db)
        self.temp_root = temp_root

    def has_business_content(self) -> bool:
        """Return whether the database already contains usable content."""
        source_exists = (
            self.db.query(Deck.id)
            .filter(Deck.type == "source")
            .limit(1)
            .first()
            is not None
        )
        card_exists = self.db.query(Card.id).limit(1).first() is not None
        return source_exists and card_exists

    def _make_temp_dir(self) -> tempfile.TemporaryDirectory[str]:
        if self.temp_root is not None:
            self.temp_root.mkdir(parents=True, exist_ok=True)
            return tempfile.TemporaryDirectory(dir=self.temp_root)
        return tempfile.TemporaryDirectory()

    def _upload_placeholder_audio(self) -> list[str]:
        uploaded_paths: list[str] = []
        with self._make_temp_dir() as temp_dir:
            temp_path = Path(temp_dir)
            for spec in MINIMAL_CARD_SPECS:
                wav_path = generate_placeholder_wav(
                    temp_path / Path(spec.audio_object_path).name,
                    frequency_hz=spec.frequency_hz,
                )
                if not self.oss_adapter.upload_file_from_path(
                    str(wav_path),
                    spec.audio_object_path,
                ):
                    raise RuntimeError(
                        f"Failed to upload placeholder audio to {spec.audio_object_path}"
                    )
                uploaded_paths.append(spec.audio_object_path)
        return uploaded_paths

    def _create_minimal_content(self) -> None:
        source = self.deck_repo.create(
            title=SEED_SOURCE_TITLE,
            type="source",
            level_index=0,
        )
        unit = self.deck_repo.create(
            title=SEED_UNIT_TITLE,
            type="unit",
            parent_id=source.id,
            level_index=0,
        )
        lesson = self.deck_repo.create(
            title=SEED_LESSON_TITLE,
            type="lesson",
            parent_id=unit.id,
            level_index=0,
        )

        for spec in MINIMAL_CARD_SPECS:
            card = self.card_repo.create(
                deck_id=lesson.id,
                card_index=spec.card_index,
                front_text=spec.front_text,
                back_text=spec.back_text,
                audio_path=spec.audio_object_path,
            )
            self.srs_repo.upsert(
                card_id=card.id,
                state="learning",
                step=0,
                stability=None,
                difficulty=None,
                due=app_now(self.db),
                last_review=None,
            )

    def seed(self, if_empty: bool = False) -> SeedReport:
        """Seed the database with minimal content and placeholder audio."""
        if self.has_business_content():
            return SeedReport(
                seeded=False,
                reason=(
                    "business content already exists"
                    if if_empty
                    else "business content already exists; seed skipped"
                ),
                source_count=self.db.query(Deck).filter(Deck.type == "source").count(),
                card_count=self.db.query(Card).count(),
                audio_object_paths=[],
            )

        uploaded_paths = self._upload_placeholder_audio()

        try:
            self._create_minimal_content()
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        return SeedReport(
            seeded=True,
            reason="minimal demo content created",
            source_count=self.db.query(Deck).filter(Deck.type == "source").count(),
            card_count=self.db.query(Card).count(),
            audio_object_paths=uploaded_paths,
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed minimal LanGear demo content")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Only seed when the database does not already contain source and card data.",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        report = MinimalContentSeeder(db).seed(if_empty=args.if_empty)
    finally:
        db.close()

    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
