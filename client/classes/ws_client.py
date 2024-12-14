
import socket
import os  # For generating the random masking key



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
        
    def listen_for_ws_msg(self):

        if not self.connected:
            raise ValueError('You are not connected yet.')

        print("Listening for websocket messages from the server...")

        #TODO - Handle messages from the ws server

        pass

    def send_ws_msg(self, data):

        if not self.connected:
            raise ValueError('You are not connected yet.')
        
        # First byte = FIN and Opcode
        byte1 = 0x81 # 10000001 => FIN = 1 and Opcode = 1 (text). FIN is the first bit in the byte. Opcode is the last bit.

        # Frame structure:
        frame = bytearray([byte1])

        # Prepare the payload (encode to utf-8)
        payload = data.encode('utf-8')
        payload_length = len(payload)

        # Handling length of payload in WebSocket frame
        if payload_length <= 125:

            frame.append(payload_length | 0x80) # In this case, the first bit will be 1 (meaning that its masked) and the rest of the bits are for the payload length.

        elif payload_length <= 65535:

            frame.append(126 | 0x80)  # 0x7E for 2-byte length encoding. It signals that we will be using 2 bytes for the payload length.

            #?? Fitting the payload length into 2 bytes, because its too big to put into 1.
            frame.append((payload_length >> 8) & 0xFF)  # Most significant byte of length
            frame.append(payload_length & 0xFF)  # Least significant byte of length

        else:
            frame.append(127 | 0x80)  # 0x7F for 8-byte length encoding (larger payloads)

            # 8-byte encoding for lengths greater than 65535
            for i in range(8):

                # Essentially, appends a byte representing a 8 bit slot in the payload length. Starting from the left-most.
                frame.append(
                    (payload_length >> (8 * (7 - i))) & 0xFF
                )

        # Generate a random masking key (4 bytes)
        masking_key = os.urandom(4)

        # Append the masking key to the frame
        frame.extend(masking_key)

         # Apply the masking key to the payload
        masked_payload = bytearray()
        for i, byte in enumerate(payload):
            masked_payload.append(byte ^ masking_key[i % 4])

        # Add the payload (the actual message in UTF-8 bytes)
        frame.extend(masked_payload)

        # Send the frame over the socket
        self.socket.sendall(frame)

        print(f"Sent message: {data}")