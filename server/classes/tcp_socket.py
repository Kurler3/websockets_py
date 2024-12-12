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

        decoded_strs = [string.strip() for string in data.decode('utf-8').split('\n') if string.strip() != '']

        # If didn't get any proper strings from the data, just return
        if not decoded_strs: return

        # First item in the array needs to be the method, the resource and the protocol.
        request_line = decoded_strs[0]

        request_line_arr = request_line.split(' ')

        if len(request_line_arr) != 3:
            self._refuse_ws_connection(conn, addr)
            return

        method, resource, protocol = request_line_arr

        if method != 'GET' and protocol != "HTTP/1.1":
            self._refuse_ws_connection(conn, addr)

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

        #TODO

        print('HEADERS: ', headers)
    
        #TODO - After everything is ok, append the addr to the ws_clients and send a response back to the client accepting the ws upgrade.
        
        pass

    def _refuse_ws_connection(self, conn, addr):
        print(f'Refusing connection for addr: {addr}')
        conn.sendall('I refuse to connect with you, I don\'t like you')
    
    #TODO
    def _send_websocket_handshake(self, data):
        pass
        
    #TODO
    def _handle_ws_frame(self, conn, addr, data):
        pass
