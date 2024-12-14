from client.classes.ws_client import WSClient
import sys


if len(sys.argv) != 3:
    print("Usage: python script.py <host> <port>")
    sys.exit(1)

host = sys.argv[1]
port = int(sys.argv[2])

if __name__ == "__main__":
    
    client = WSClient()
    
    client.connect(host, port)

    # Keep sending messages on the websocket connection.    
    if client.connected:
        
        # Start listening for websocket messages from the server.
        client.listen_for_ws_msg()

        while True:
            input_for_ws = input('What would you like to send to the websocket server? ')

            # Send msg.
            client.send_ws_msg(input_for_ws)