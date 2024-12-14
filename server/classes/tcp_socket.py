import socket
import threading
import base64
import hashlib
from utils.http_parser import parse_http_request


class TCPSocket:

    def __init__(self, host="127.0.0.1", port=443, max_connections=5, buffer_size=1024):
        self.host = host
        self.port = port
        self.backlog = max_connections
        self.buffer_size = buffer_size
        self.socket = None
        self.ws_clients = set()

    def start_server(self):
        try:

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.backlog)
            print(f'Server started on {self.host}:{self.port}')
            self._accept_connections()

        except Exception as e:
            print(f'An error ocurred while starting the server: {e}')
        finally:
            if self.socket:
                self.socket.close()
                print('Socket server closed.')

    def _accept_connections(self):
        while True:
            try:
                conn, addr = self.socket.accept()
                print(f"Connected by {addr}")

                # Start a new thread for each client
                client_thread = threading.Thread(
                    target=self._handle_client, args=(conn, addr))

                # Ensure threads close with the main program
                client_thread.daemon = True

                # Start the thread
                client_thread.start()

            except Exception as e:
                print(f'An error occurred while accepting connection: {e}')

    def _handle_client(self, conn, addr):
        """Handle communication with a single client."""
        try:
            with conn:
                while True:

                    data = conn.recv(self.buffer_size)

                    if not data:
                        raise Exception('Connection closed')

                    self._process_data(conn, addr, data)
        except ConnectionResetError:
            print(f"Connection with {addr} was forcibly closed.")
        except Exception as e:
            print(f"An unexpected error occurred with {addr}: {e}")
        finally:
            print(f"Connection closed with: {addr}")

    def _process_data(self, conn, addr, data):

        # If the address is not in the ws_clients set, then need to parse the data as an http string.
        if addr not in self.ws_clients:
            self._handle_handshake(conn, addr, data)
        else:
            self._handle_ws_frame(conn, addr, data)

    def _handle_handshake(self, conn, addr, data):

        try:

            method, resource, protocol, headers = parse_http_request(data)

            ##################################################################
            ## CHECK THAT THE HEADERS ARE ALL OK FOR THE HANDSHAKE ###########
            ##################################################################

            # Check the upgrade header.
            if headers.get("Upgrade", "").lower() != "websocket":
                raise Exception("Missing or invalid 'Upgrade' header")

            # Check the upgrade header
            if "upgrade" not in headers.get("Connection", "").lower():
                raise Exception("Missing or invalid 'Connection' header")

            # Check the websocket key. (will be used in the Sec-Websocket-Accept header)
            key = headers.get("Sec-WebSocket-Key", "")
            try:
                decoded_key = base64.b64decode(key)
                if len(decoded_key) != 16:  # WebSocket keys are 16 bytes
                    raise ValueError
            except Exception:
                raise ValueError("Invalid 'Sec-WebSocket-Key' header")

            # Check the websocket version. Needs to be 13.
            if headers.get("Sec-WebSocket-Version", "") != "13":
                raise ValueError("Unsupported 'Sec-WebSocket-Version'")

            # Accept handshake
            self._accept_handshake(conn, addr, ws_key=key)

        except Exception as e:
            print(f'Exception while handling handshake {e}')
            self._refuse_ws_connection(conn, addr)

    def _refuse_ws_connection(self, conn, addr):
        print(f'Refusing connection for addr: {addr}')
        conn.sendall('I refuse to connect with you, I don\'t like you')

    def _accept_handshake(self, conn, addr, ws_key):

        # HTTP/1.1 101 Switching Protocols
        # Upgrade: websocket
        # Connection: Upgrade
        # Sec-WebSocket-Accept: <calculated_value>

        accept_key = self._calculate_accept_key(ws_key)

        conn.sendall(f"""
            HTTP/1.1 101 Switching Protocols
            Upgrade: websocket
            Connection: Upgrade
            Sec-WebSocket-Accept: {accept_key}
        """.encode('utf-8'))

        self.ws_clients.add(addr)

    def _calculate_accept_key(self, key):
        magic_string = '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
        concatenated = key + magic_string
        hashed = hashlib.sha1(concatenated.encode('utf-8')).digest()
        return base64.b64encode(hashed).decode('utf-8')

    # TODO

    def _handle_ws_frame(self, conn, addr, data):
        """Decodes a single WebSocket frame received from the connection."""

        if len(data) < 2:
            raise ValueError("Incomplete frame header received.")

        # Extract header information (first byte: FIN, opcode, etc., second byte: mask & length)
        byte1, byte2 = data[:2]

        # FIN: Most significant bit in byte1
        fin = (byte1 & 0b10000000) >> 7

        # Opcode: Last 4 bits in byte1
        opcode = byte1 & 0x0F

        print('FIN AND OPCODE: ', fin, opcode)

        # Check if it's a Close frame
        if opcode == 0x8:
            raise ValueError("Received Close frame")

        # Mask bit: Most significant bit in byte2
        mask = (byte2 >> 7) & 0x01

        # Extract the Payload length: Remaining 7 bits of byte2
        payload_length = byte2 & 0x7F

        # If Payload Length is 126 or 127, we'll need to read additional bytes
        length_offset = 2  # Default starting point for payload length

        if payload_length == 126:

            # If less than 4 bytes, there's data missing, because in this case, there's an extension of 2 bytes for the payload length.
            if len(data) < 4:
                raise ValueError("Incomplete frame: 2-byte length extension required.")

            # To create a hexadecimal, move the first byte to the left and append the second byte.
            payload_length = (data[2] << 8) + data[3]  # 16-bit length
            
            # Now its 4 bytes just for the payload_length and the headers
            length_offset = 4

        elif payload_length == 127:

            if len(data) < 10:
                raise ValueError(
                    "Incomplete frame: 8-byte length extension required.")
            
            # 64-bit length in the next 8 bytes
            payload_length = (
                (data[2] << 56) | (data[3] << 48) | (data[4] << 40) |
                (data[5] << 32) | (data[6] << 24) | (data[7] << 16) |
                (data[8] << 8) | data[9]
            )

            length_offset = 10

        # Extract the mask key (4 bytes if mask bit is set)
        if mask:
            mask_key = data[length_offset:length_offset+4]
            mask_offset = length_offset + 4
        else:
            mask_key = None
            mask_offset = length_offset

        # Extract the payload data (Message)
        payload = data[mask_offset:mask_offset + payload_length]

        # If mask is set, apply the mask key to the payload
        if mask:
            payload = bytearray([byte ^ mask_key[i % 4]
                                for i, byte in enumerate(payload)])

        # Convert the payload back to a string (assuming UTF-8 encoding for text messages)
        decoded_message = payload.decode('utf-8')

        print(f'Decoded message from ws: ', decoded_message)

        # Return the decoded message
        return decoded_message
