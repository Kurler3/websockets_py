import socket
import threading
import base64
import hashlib

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
                client_thread = threading.Thread(target=self._handle_client, args=(conn,addr))
                
                # Ensure threads close with the main program
                client_thread.daemon = True  

                # Start the thread
                client_thread.start()

            except Exception as e:
                print(f'An error occurred while accepting connection: {e}')
    
    def _handle_client(self, conn, addr):
        """Handle communication with a single client."""
        with conn:
            while True:
                data = conn.recv(self.buffer_size)
                if not data:
                    print(f'Connection closed with: {addr}')
                    break
                print(f"Received: {data}")
                self._process_data(conn, addr, data)
    
    def _process_data(self, conn, addr, data):
        # If the address is not in the ws_clients set, then need to parse the data as an http string.
        if addr not in self.ws_clients:
            self._handle_handshake(conn, addr, data)
        else:
            self._handle_ws_frame(conn, addr, data)

    def _handle_handshake(self, conn, addr, data):

        decoded_strs = [string.strip() for string in data.decode('utf-8').split('\n') if string.strip() != '']

        # If didn't get any proper strings from the data, just return
        if not decoded_strs: return

        # First item in the array needs to be the method, the resource and the protocol.
        request_line = decoded_strs[0]

        request_line_arr = request_line.split(' ')

        if len(request_line_arr) != 3:
            self._refuse_ws_connection(conn, addr)
            raise ValueError('Invalid HTTP Request')

        method, resource, protocol = request_line_arr

        if method != 'GET' and protocol != "HTTP/1.1":
            self._refuse_ws_connection(conn, addr)
            raise Exception('Invalid HTTP Request')

        # Rest is whatever headers were passed. Make sure that there's the necessary ones for the connection. 
        decoded_strs = decoded_strs[1:]

        # Init dict to store all the headers.
        headers = {}

        for header_line in decoded_strs:
            header, value = header_line.split(': ')
            headers[header] = value

        ##################################################################
        ## CHECK THAT THE HEADERS ARE ALL OK FOR THE HANDSHAKE ###########
        ##################################################################

        # Check the upgrade header.
        if headers.get("Upgrade", "").lower() != "websocket":
            msg = "Missing or invalid 'Upgrade' header"
            print(msg)
            self._refuse_ws_connection(conn, addr)
            raise Exception(msg)

        # Check the upgrade header
        if "upgrade" not in headers.get("Connection", "").lower():
            msg = "Missing or invalid 'Connection' header"
            print(msg)
            self._refuse_ws_connection(conn, addr)
            raise Exception(msg)
        
        # Check the websocket key. (will be used in the Sec-Websocket-Accept header)
        key = headers.get("Sec-WebSocket-Key", "")
        try:
            decoded_key = base64.b64decode(key)
            if len(decoded_key) != 16:  # WebSocket keys are 16 bytes
                raise ValueError
        except Exception:
            self._refuse_ws_connection(conn, addr)
            raise ValueError("Invalid 'Sec-WebSocket-Key' header")

        # Check the websocket version. Needs to be 13.
        if headers.get("Sec-WebSocket-Version", "") != "13":
            self._refuse_ws_connection(conn, addr)
            raise ValueError("Unsupported 'Sec-WebSocket-Version'")


        # Accept handshake
        self._accept_handshake(conn, addr, ws_key=key)

        

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


    #TODO
    def _handle_ws_frame(self, conn, addr, data):
        pass
