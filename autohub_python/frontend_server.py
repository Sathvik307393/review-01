import http.server
import socketserver
import time

PORT = 5000

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        ts = time.strftime("%H:%M:%S")
        print(f"  [{ts}] [FrontendServer] {self.command} {self.path}  →  {args[1] if len(args)>1 else ''}")

if __name__ == "__main__":
    # socketserver TCPServer allows rebinding address immediately
    socketserver.TCPServer.allow_reuse_address = True
    handler = FrontendHandler
    try:
        with socketserver.TCPServer(("", PORT), handler) as httpd:
            print(f"Frontend Static Server listening on port {PORT}...")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down Frontend Static Server.")
