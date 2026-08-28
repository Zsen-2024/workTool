import unittest
from unittest.mock import MagicMock, patch

from app.tools.netease_music import client


class TestWeapiEncrypt(unittest.TestCase):
    def test_weapi_payload_has_params_and_encSecKey(self):
        payload = client._weapi_encrypt({"foo": "bar"})
        self.assertIn("params", payload)
        self.assertIn("encSecKey", payload)
        self.assertTrue(payload["params"])
        self.assertTrue(payload["encSecKey"])
        self.assertEqual(len(payload["encSecKey"]), 256)


class TestPlaylistPaging(unittest.TestCase):
    def test_slice_page(self):
        items = [client.SongItem(i, f"n{i}", "a", 1000) for i in range(1, 71)]
        page2 = client._slice_page(items, page=2, page_size=30, total=70)
        self.assertEqual(len(page2.songs), 30)
        self.assertEqual(page2.songs[0].id, 31)
        self.assertEqual(page2.total, 70)
        self.assertEqual(page2.page, 2)


class TestFetchSongUrl(unittest.TestCase):
    @patch("app.tools.netease_music.client.requests.post")
    def test_empty_url_raises_lookup(self, mock_post):
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = {"data": [{"id": 1, "url": None}]}
        mock_post.return_value = resp
        with self.assertRaises(LookupError):
            client.fetch_song_url(1)


if __name__ == "__main__":
    unittest.main()
