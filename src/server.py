import functools
import os.path
try:
    import http.server as compat_http_server
except ImportError:
    import BaseHTTPServer as compat_http_server

from config import PORT
from common import full_path


# BaseHTTPRequestHandler is an old-style class, which fails super()
# http://stackoverflow.com/a/11810015/3786245
class Handler(compat_http_server.BaseHTTPRequestHandler, object):
    def __init__(self, *args, **kwargs):
        self.swf_path = kwargs['swf_path']
        del kwargs['swf_path']

        self.collected_data = kwargs['collected_data']
        del kwargs['collected_data']

        files = [self.swf_path, '/proxy.pac']

        self.files_dict = {
            filename: full_path(os.path.basename(filename))
            for filename in files
        }

        super(Handler, self).__init__(*args, **kwargs)

    def do_GET(self):
        if self.path in self.files_dict:
            self.send_response(200)
            self.end_headers()

            cur_file = self.files_dict[self.path]

            if os.path.exists(cur_file + '.in'):
                with open(cur_file + '.in', 'rb') as f:
                    content = f.read().decode('utf-8')
                content = content.replace(
                    '$PORT$', str(PORT)).replace('$SWF_PATH$', self.swf_path)
                content = content.encode('utf-8')
            else:
                with open(cur_file, 'rb') as f:
                    content = f.read()

            self.wfile.write(content)
        else:
            self.send_error(404)
            return

    def do_POST(self):
        length = int(self.headers.get('Content-Length', None))
        cur_data = self.rfile.read(length).decode('utf-8')
        self.send_response(200)
        self.end_headers()

        print(cur_data)
        self.collected_data.append(cur_data)

    def log_message(self, *args, **kwargs):
        pass


def run_server(swf_path, lock, data_count=1):
    lock.acquire()

    collected_data = []

    httpd = compat_http_server.HTTPServer(
        ('', PORT), functools.partial(
            Handler, swf_path=swf_path, collected_data=collected_data))

    print('serving at port %d' % PORT)

    while len(collected_data) < data_count:
        httpd.handle_request()

    print('Proxy server done')
    lock.release()

    return collected_data
