import uuid
from contextlib import contextmanager

import models
from typing import Iterator

from sqlalchemy import create_engine, select, and_, func
from sqlalchemy.orm import Session, sessionmaker
from config import DATABASE_URL

_engine = create_engine(DATABASE_URL)
_session = sessionmaker(_engine, expire_on_commit=False)


# Dependency
@contextmanager
def get_db() -> Iterator[Session]:
    """
    Dependency function that yields db sessions
    """
    with _session() as session:
        yield session
        session.commit()


def get_albums_not_completed(db: Session) -> models.TaskTrackerAlbum | None:
    query = select(models.TaskTrackerAlbum).where(models.TaskTrackerAlbum.completed.is_(False)).order_by(
        models.TaskTrackerAlbum.updated_at.asc()).limit(1)
    return db.scalars(query).one_or_none()


def get_or_create_album_by_params(
        db: Session,
        tg_id: str | None,
        spotify_album_id: str | None,
        type: str | None,
) -> models.TaskTrackerAlbum:
    query = select(models.TaskTrackerAlbum).where(
        and_(
            models.TaskTrackerAlbum.spotify_album_id == spotify_album_id,
            models.TaskTrackerAlbum.type == type,
        )
    ).order_by(models.TaskTrackerAlbum.updated_at.asc()).limit(1)
    task = db.scalars(query).one_or_none()
    if task is not None:
        return task
    task = models.TaskTrackerAlbum(
        id=uuid.uuid4(),
        tg_id=tg_id,
        type=type,
        spotify_album_id=spotify_album_id,
        yandex_music_album_id=None,
        completed=False,
    )
    db.add(task)
    db.commit()
    return task


def get_or_create_track_by_params(
        db: Session,
        tg_id: str | None,
        spotify_album_id: str | None,
        spotify_track_id: str | None,
        yandex_music_album_id: str | None,
) -> models.TaskTrackerTrack:
    query = select(models.TaskTrackerTrack).where(
        and_(
            models.TaskTrackerTrack.tg_id == tg_id,
            models.TaskTrackerTrack.spotify_album_id == spotify_album_id,
            models.TaskTrackerTrack.spotify_track_id == spotify_track_id,
            models.TaskTrackerTrack.yandex_music_album_id == yandex_music_album_id,
        )
    ).order_by(models.TaskTrackerTrack.updated_at.asc()).limit(1)
    task = db.scalars(query).one_or_none()
    if task is not None:
        return task
    task = models.TaskTrackerTrack(
        id=uuid.uuid4(),
        tg_id=tg_id,
        spotify_album_id=spotify_album_id,
        spotify_track_id=spotify_track_id,
        yandex_music_album_id=yandex_music_album_id,
        yandex_music_track_id=None,
        completed=False,
    )
    db.add(task)
    db.commit()
    return task


def get_track_not_completed(db: Session) -> models.TaskTrackerTrack | None:
    query = select(models.TaskTrackerTrack).where(models.TaskTrackerTrack.completed.is_(False)).order_by(
        models.TaskTrackerTrack.updated_at.asc()).limit(1)
    return db.scalars(query).one_or_none()


def get_or_create_user_model(
        db: Session,
        user_id: str | None,
) -> models.TaskUserInfo:
    query = select(models.TaskUserInfo).where(
        and_(
            models.TaskUserInfo.user_id == user_id,
        )
    ).order_by(models.TaskUserInfo.updated_at.asc()).limit(1)
    entity = db.scalars(query).one_or_none()
    if entity is not None:
        return entity
    entity = models.TaskUserInfo(
        id=uuid.uuid4(),
        user_id=user_id,
    )
    db.add(entity)
    db.commit()
    return entity


def get_list_relations_tracks(
        db: Session,
        user_id: str | None,
) -> str:
    formated = []
    query = select(models.TaskTrackerAlbum).where(
        and_(
            models.TaskTrackerAlbum.tg_id == user_id,
        )
    ).order_by(models.TaskTrackerAlbum.created_at.asc()).limit(5)
    entities = db.scalars(query).all()
    for entity in entities:
        query = select(func.count(models.TaskTrackerTrack.id).label('count')).where(
            and_(
                models.TaskTrackerTrack.spotify_album_id == entity.spotify_album_id,
                models.TaskTrackerTrack.tg_id == entity.tg_id,
            ),
        )
        _all = db.scalars(query).one()
        query = select(func.count(models.TaskTrackerTrack.id).label('count')).where(
            and_(
                models.TaskTrackerTrack.spotify_album_id == entity.spotify_album_id,
                models.TaskTrackerTrack.tg_id == entity.tg_id,
                models.TaskTrackerTrack.completed.is_(True),
            ),
        )
        _completed = db.scalars(query).one()
        formated.append(
            f"[{entity.spotify_album_id}] [{_completed} / {_all}]"
        )
    return "\n".join(formated)


if __name__ == "__main__":
    models.Base.metadata.create_all(_engine)
