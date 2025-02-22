"""
Перед использованием настрой env

https://yandex-music.readthedocs.io/en/latest/token.html
https://developer.spotify.com

"""
import io
import time
import uuid
from pathlib import Path

import requests
from spotdl import Spotdl, Song
from spotipy import Spotify, SpotifyClientCredentials
from sqlalchemy.orm import Session

import models
import queries
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, YANDEX_MUSIC_TOKEN
from ya_music import YaMusicClient

# Инициализация Spotify
sp = Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    )
)
_spotdl = None


def get_spotdl() -> Spotdl:
    global _spotdl
    # Инициализация spotdl
    if _spotdl is not None:
        return _spotdl
    # Настройки для spotdl
    downloader_settings = {
        "format": "mp3",
        # Простой интерфейс для отображения прогресса
        "simple_tui": False,
    }

    _spotdl = Spotdl(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        no_cache=True,
        headless=True,
        downloader_settings=downloader_settings,
    )

    return _spotdl


def download_image(url: str) -> io.BytesIO:
    """
    Скачивает изображение по URL и возвращает его как объект io.BytesIO.

    :param url: URL изображения.
    :return: Объект io.BytesIO с содержимым изображения.
    """
    response = requests.get(url)
    if response.status_code == 200:
        # Создаем объект BytesIO и записываем в него данные
        image_data = io.BytesIO(response.content)
        image_data.seek(0)  # Перемещаем указатель в начало
        return image_data
    else:
        raise Exception(f"Ошибка при загрузке изображения: {response.status_code}")


def download_spotify_track(track_id: str) -> tuple[Song | None, Path | None]:
    """
    Скачивает трек из Spotify по ссылке.

    :param track_id: id трека на Spotify.
    :return: Путь к скачанному файлу.
    """
    track_url = f"https://open.spotify.com/track/{track_id}"
    spotdl = get_spotdl()
    try:
        # Скачивание трека
        print(f"Скачивание трека: {track_url}")
        song = spotdl.search([track_url])[0]
        path = spotdl.download(song)
        print(f"Трек успешно скачан: {track_url}")
        return path
    except Exception as e:
        print(f"Ошибка при скачивании трека: {e}")
        return None, None


def spotify_get_album(_id: str, _type: str):
    print(f"Получение spotify плейлиста/альбома по {_id=} {_type=}")
    if _type == models.TaskTrackerAlbumType.album.value:
        return sp.album(_id)
    if _type == models.TaskTrackerAlbumType.playlist.value:
        return sp.playlist(_id)
    raise TypeError("I'm not found type")


def spotify_get_album_tracks(_id: str, _type: str) -> list[str]:
    print(f"Получение spotify плейлиста/альбома по {_id=} {_type=}")
    if _type == models.TaskTrackerAlbumType.album.value:
        tracks = sp.album_tracks(_id, limit=50, offset=0)
        return [track['id'] for track in tracks['items']]
    if _type == models.TaskTrackerAlbumType.playlist.value:
        tracks = sp.playlist_items(_id, limit=100, offset=0)
        return [track["track"]['id'] for track in tracks['items']]
    raise TypeError("I'm not found type")


def from_album_to_spotify(db: Session) -> int:
    """
    Функция переносит ID шники из спотифая в yandex music
    :param db:
    :return:
    """
    task = queries.get_albums_not_completed(db=db)
    if task is None:
        return 0
    user = queries.get_or_create_user_model(db=db, user_id=task.tg_id)
    # Инициализация Яндекс.Музыки
    yandex_client = YaMusicClient(user.yandex_access_token).init()
    # Получает информацию об альбоме из Spotify
    album_info = spotify_get_album(task.spotify_album_id, task.type)
    if task.yandex_music_album_id is None:
        playlist = yandex_client.users_playlists_create(
            title=album_info["name"] or uuid.uuid4(),
            visibility='public',
        )  # Создаем плейлист в яндекс музыке
        task.yandex_music_album_id = playlist.playlist_id
        db.add(task)
        db.commit()
    # Скачиваем обложку альбома
    cover_url = album_info['images'][0]['url']
    yandex_client.upload_cover(
        bytes_io=download_image(cover_url),
        playlist_id=task.yandex_music_album_id,
    )
    tracks_ids = spotify_get_album_tracks(task.spotify_album_id, task.type)
    for track_id in tracks_ids:
        queries.get_or_create_track_by_params(
            db=db,
            tg_id=task.tg_id,
            spotify_album_id=task.spotify_album_id,
            spotify_track_id=track_id,
            yandex_music_album_id=task.yandex_music_album_id,
        )
    task.completed = True
    db.add(task)
    db.commit()
    print(f"Созданы задачи на перенос треков из альбома {task.spotify_album_id}")
    return 1


def from_track_to_spotify(db: Session):
    """
    Функция переносит ID шники из спотифая в yandex music
    :param db:
    :return:
    """
    task = queries.get_track_not_completed(db=db)
    if task is None:
        return 0
    if task.spotify_track_id is None:
        task.completed = True
        db.add(task)
        db.commit()
        return None
    song, path = download_spotify_track(track_id=task.spotify_track_id)
    if path is None or song is None:
        print(f"Произошла ошибка при загрузки трека на local из spotify {task.spotify_track_id}")
        return 1
    user = queries.get_or_create_user_model(db=db, user_id=task.tg_id)
    # Инициализация Яндекс.Музыки
    yandex_client = YaMusicClient(user.yandex_access_token).init()
    task.yandex_music_track_id = yandex_client.upload_track(
        path=path,
        playlist_id=task.yandex_music_album_id,
    )
    task.completed = True
    db.add(task)
    db.commit()
    print(f"Трек успешно загружен в яндекс музыку {song.name}")
    return 1


def loop():
    result = 1
    while result > 0:
        result = 0
        try:
            with queries.get_db() as db:
                result += from_album_to_spotify(db=db)
            with queries.get_db() as db:
                result += from_track_to_spotify(db=db)
        except Exception:
            import traceback
            traceback.print_exc()
            result = 1
            time.sleep(1)


def loop_forever():
    while True:
        loop()
        time.sleep(5 * 60)


def add_task_album(user_id: str, url: str):
    for _type in models.TaskTrackerAlbumType:
        try:
            album = spotify_get_album(url, _type.value)
            with queries.get_db() as db:
                queries.get_or_create_album_by_params(
                    db=db,
                    tg_id=user_id,
                    spotify_album_id=album["id"],
                    type=_type.value,
                )
            return None
        except Exception:
            pass
    else:
        raise TypeError("Не найдено подходящего типа для ссылки")
