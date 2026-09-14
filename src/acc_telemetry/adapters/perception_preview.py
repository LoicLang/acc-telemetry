"""Optional localhost-only, read-only preview with HTTP byte ranges for video seeking."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import re


class RangeHandler(SimpleHTTPRequestHandler):
    def send_head(self):
        self.remaining=None
        root=Path(self.directory).resolve()
        path=Path(self.translate_path(self.path)).resolve()
        if not path.is_relative_to(root):
            self.send_error(403,'Outside preview directory');return None
        if path.is_dir():path=(path/'index.html').resolve()
        if not path.is_relative_to(root):
            self.send_error(403,'Outside preview directory');return None
        if not path.is_file():
            self.send_error(404);return None
        size=path.stat().st_size;start=0;end=size-1
        request=self.headers.get('Range')
        if request:
            match=re.fullmatch(r'bytes=(\d*)-(\d*)',request.strip())
            if not match or not any(match.groups()):
                self.send_error(416);return None
            left,right=match.groups()
            if left:
                start=int(left);end=min(int(right),size-1) if right else size-1
            else:
                length=int(right);start=max(0,size-length);end=size-1
                if length==0:start=size
            if start>=size or end<start:
                self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
        stream=path.open('rb')
        self.send_response(206 if request else 200)
        self.send_header('Content-Type',self.guess_type(str(path)))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Content-Length',str(end-start+1))
        if request:self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers();stream.seek(start);self.remaining=end-start+1
        return stream

    def copyfile(self,source,outputfile):
        remaining=self.remaining
        while remaining:
            block=source.read(min(65536,remaining))
            if not block:break
            outputfile.write(block);remaining-=len(block)


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory',required=True)
    p.add_argument('--port',type=int,default=8767)
    a=p.parse_args(argv);root=Path(a.directory).resolve()
    if not root.is_dir():p.error('preview directory not found')
    server=ThreadingHTTPServer(('127.0.0.1',a.port),partial(RangeHandler,directory=str(root)))
    print(f'http://127.0.0.1:{server.server_port}/',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
