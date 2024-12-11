from classes.ws_client import WSClient
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
