"""Development server bound to localhost; not suitable for deployment."""
import argparse
import json
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import library

ROOT=Path(__file__).resolve().parent

def handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def reply(self, status, value, kind='application/json; charset=utf-8'):
            payload=json.dumps(value).encode() if kind.startswith('application/json') else value
            self.send_response(status); self.send_header('Content-Type',kind)
            self.send_header('Content-Length',str(len(payload))); self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff'); self.end_headers(); self.wfile.write(payload)
        def do_GET(self):
            if self.path == '/api/state':
                return self.reply(200,library.snapshot(db_path))
            if self.path in ('/','/index.html','/app.js','/style.css'):
                filename='index.html' if self.path=='/' else self.path[1:]
                kind={'index.html':'text/html','app.js':'text/javascript','style.css':'text/css'}[filename]+'; charset=utf-8'
                return self.reply(200,(ROOT/filename).read_bytes(),kind)
            self.reply(404,{'error':'Not found'})
        def do_POST(self):
            try:
                if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
                    return self.reply(415,{'error':'JSON required'})
                length=int(self.headers.get('Content-Length','0'))
                if not 0 < length <= 16384: raise ValueError('Invalid body size')
                payload=json.loads(self.rfile.read(length))
                if not isinstance(payload,dict): raise ValueError('Object required')
                routes={'/api/books':lambda:library.add_book(db_path,payload.get('title'),payload.get('total')),
                        '/api/members':lambda:library.add_member(db_path,payload.get('name')),
                        '/api/borrow':lambda:library.borrow(db_path,payload.get('book_id'),payload.get('member_id'),payload.get('due')),
                        '/api/return':lambda:library.return_loan(db_path,payload.get('loan_id'))}
                if self.path not in routes:return self.reply(404,{'error':'Not found'})
                routes[self.path]();self.reply(200,{'ok':True})
            except (ValueError,TypeError,json.JSONDecodeError) as exc:self.reply(400,{'error':str(exc)})
            except sqlite3.Error:self.reply(500,{'error':'Database error'})
    return Handler

def main():
    p=argparse.ArgumentParser();p.add_argument('--db',default='library.sqlite3');p.add_argument('--port',type=int,default=8765);args=p.parse_args()
    library.initialize(args.db)
    with ThreadingHTTPServer(('127.0.0.1',args.port),handler(args.db)) as server:
        print('Local demo: http://127.0.0.1:'+str(server.server_port),flush=True);server.serve_forever()
if __name__=='__main__':main()
