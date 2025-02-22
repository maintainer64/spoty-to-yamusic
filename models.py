import re
import uuid
from datetime import datetime, UTC
from enum import Enum

from sqlalchemy import UUID, func, VARCHAR, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, declared_attr


class Base(DeclarativeBase):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(UTC), server_default=func.now())

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now(UTC),
        onupdate=datetime.now(UTC),
    )
    __name__: str  # type: ignore[misc]

    # Generate __tablename__ automatically
    @declared_attr.directive
    def __tablename__(cls) -> str:
        name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", cls.__name__)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


class TaskTrackerAlbumType(str, Enum):
    playlist = "playlist"
    album = "album"


class TaskTrackerAlbum(Base):
    tg_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=False)
    type: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    spotify_album_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    yandex_music_album_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)


class TaskTrackerTrack(Base):
    tg_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=False)
    spotify_album_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    spotify_track_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    yandex_music_album_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    yandex_music_track_id: Mapped[str | None] = mapped_column(VARCHAR(), index=True, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean(), nullable=False, default=False)
