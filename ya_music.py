import io
import pathlib
import yandex_music


class YaMusicClient(yandex_music.Client):

    @yandex_music.client.log
    def upload_track(
            self,
            path: pathlib.Path,
            playlist_id: str,
    ) -> str:
        """Загрузка трека в альбом.

        Args:
            path (:obj:`str`): Путь до файла скаченного.
            playlist_id (:obj:`str`): Идентификатор полного плейлиста.
        """
        owner_id, _ = playlist_id.split(":")
        params = {
            "uid": owner_id,
            "playlist-id": playlist_id,
            "path": path.name,
        }

        url = f'{self.base_url}/loader/upload-url'

        result_init = self._request.post(
            url,
            params,
        )
        url_download = result_init["post_target"]
        track_id = result_init["ugc_track_id"]

        result_download = self._request.post(
            url_download,
            files={
                "file": path.open("rb")
            }
        )

        return track_id

    @yandex_music.client.log
    def upload_cover(
            self,
            bytes_io: io.BytesIO,
            playlist_id: str,
    ) -> int:
        """Загрузка обложки в альбом.

        Args:
            bytes_io (:obj:`str`): IO контейнер.
            playlist_id (:obj:`str`): Идентификатор полного плейлиста.
        """
        bytes_io.seek(0)
        owner_id, album_id = playlist_id.split(":")
        url = f"{self.base_url}/users/{owner_id}/playlists/{album_id}/cover/upload"

        response = self._request.post(
            url,
            files={
                "image": bytes_io
            },
        )
        return response["uid"]
