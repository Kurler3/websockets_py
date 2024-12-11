import socket
import threading


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
        pass

    def _send_websocket_handshake(self, data):
        pass
    
    def _handle_ws_frame(self, conn, addr, data):
        pass
