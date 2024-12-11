

import socket


class WSClient:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self, host, port):

        self.socket.connect((host, port))

        self.socket.sendall(b"""GET /chat HTTP/1.1
                                Host: server.example.com
                                Upgrade: websocket
                                Connection: Upgrade
                                Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
                                Origin: http://example.com
                                Sec-WebSocket-Protocol: chat, superchat
                                Sec-WebSocket-Version: 13
                            """)

        
        data = self.socket.recv(1024)  # Buffer size

        print('RECEIVED BACK: ', data)
