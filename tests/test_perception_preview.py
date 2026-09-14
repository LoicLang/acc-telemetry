"""Browser video seeking needs byte ranges; the preview must stay inside its package."""
from functools import partial
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from acc_telemetry.adapters.perception_preview import RangeHandler


class TestPreview(unittest.TestCase):
    def test_byte_ranges_suffix_and_invalid_seek(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'video.mp4').write_bytes(b'0123456789')
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(RangeHandler,directory=str(root)))
            thread=Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                url=f'http://127.0.0.1:{server.server_port}/video.mp4'
                with urlopen(Request(url,headers={'Range':'bytes=2-4'})) as r:
                    self.assertEqual(r.status,206);self.assertEqual(r.read(),b'234')
                    self.assertEqual(r.headers['Content-Range'],'bytes 2-4/10')
                with urlopen(Request(url,headers={'Range':'bytes=-2'})) as r:self.assertEqual(r.read(),b'89')
                with self.assertRaises(HTTPError) as exc:urlopen(Request(url,headers={'Range':'bytes=20-'}))
                self.assertEqual(exc.exception.code,416)
                (root/'outside').symlink_to(root.parent)
                with self.assertRaises(HTTPError) as exc:urlopen(f'http://127.0.0.1:{server.server_port}/outside/')
                self.assertEqual(exc.exception.code,403)
            finally:server.shutdown();server.server_close();thread.join()
