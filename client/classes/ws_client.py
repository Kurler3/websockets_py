
import socket
import os  # For generating the random masking key
from utils.ws import encode_to_ws_frame, decode_ws_frame
import threading


class WSClient:

    def __init__(self, buffer_size=1024):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.buffer_size = buffer_size
        self.connected = False


    def connect(self, host, port):

        self.socket.connect((host, port))

        print("Trying to create websocket connection...")


        # The websocket key should be random.
        self.socket.sendall(b"""GET /chat HTTP/1.1
                                Host: server.example.com
                                Upgrade: websocket
                                Connection: Upgrade
                                Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
                                Origin: http://example.com
                                Sec-WebSocket-Protocol: chat, superchat
                                Sec-WebSocket-Version: 13
        """)

        # Receive the first http msg from the server
        data = self.socket.recv(self.buffer_size) 

        # Handle accept or refuse handshake from server.
        if not data:
            print(f'Connection refused by {host}:{port}')
            raise ValueError("WebSocket handshake failed")

        data = data.decode('utf-8')

        # Parse the http request from the server.
        if "101 Switching Protocols" in data and 'Sec-WebSocket-Accept' in data:
            print(f"Connection accepted by {host}:{port}")
            self.connected = True
        else:
            raise ValueError("WebSocket handshake failed")
        
        # Start listening for websocket messages from the server.
        listener_thread = threading.Thread(target=self.listen_for_ws_msg)
        listener_thread.daemon = True  # Allows thread to exit when the program exits
        listener_thread.start()
        
    def listen_for_ws_msg(self):

        if not self.connected:
            raise ValueError('You are not connected yet.')

        print("Listening for websocket messages from the server...")

        while True:
            
            # Handle messages from the ws server
            data = self.socket.recv(self.buffer_size)

            if not data: continue

            msg = decode_ws_frame(data)

            print('Message received: ', msg)

    def send_ws_msg(self, data):

        if not self.connected:
            raise ValueError('You are not connected yet.')

        frame = encode_to_ws_frame(data, use_mask=True)

        # Send the frame over the socket
        self.socket.sendall(frame)

        if data == "exit":
            self.socket.close()
