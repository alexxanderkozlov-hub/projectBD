from server.handler import MyHandler
from http.server import HTTPServer

server = HTTPServer(("localhost", 8000), MyHandler)

print("http://localhost:8000")
server.serve_forever()