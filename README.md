

## Websockets implementation in Python from scratch

This project defines a server tcp socket and a client that allows for the client to connect to the server.

The server accepts multiple connections, using threading.

The client can only connect to one server at a time.

This was all implement following the official specification by the internet task force: https://datatracker.ietf.org/doc/html/rfc6455

## General explanation of the project.

The implementation of websockets involves an initial handshake using HTTP, followed by messages in the socket format. These messages are broke into frames, to allow for bigger messages to be transmitted over the internet using multiples frames.

## The handhshake

In the handshake phase, the client has to send an http request of this format:

    GET /chat HTTP/1.1
    Host: server.example.com
    Upgrade: websocket
    Connection: Upgrade
    Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
    Origin: http://example.com
    Sec-WebSocket-Protocol: chat, superchat
    Sec-WebSocket-Version: 13

The following headers are required by the client:

- Upgrade: websocket. This means that the client wants the connection to be upgraded to websocket.
- Connection: Upgrade. This means that the client wants the connection to be upgraded.
- Sec-Websocket-Key: a random key. This will be later used by the server.
- Sec-WebSocket-Version: specifies the version of the websocket protocol to be used in the communication.

After the server receives this, it needs to either accept or deny the request to upgrade to websockets.

Headers to check and what to do:
- Check for "Upgrade: websocket" and "Connection: Upgrade"
- Using the "Sec-Websocket-Key", concate a magic key to it, get the hash using SHA-1 and then encode it to base64. Attach this to the header: "Sec-WebSocket-Accept"

For the client to know that the handshake was accepted, it needs to receive from the server the following http status code: 101, which means "Switching Protocols". If the client receives anything else, it will be treated as a deny of the handshake.

### Communication using frames (after the handshake)

#### Encoding the message

RFC 6455 defines frames to be encoded in the following format:

- Headers (FIN, opcode, mask bit, payload length...)
- Payload encoded as utf-8

The FIN bit defined whether this frame is the last or not for a specific message. 
It will be the first bit on the first byte of the frame.
Next is the opcode, which will be the LSB of the first byte. The opcode is used to define the type of data being passed in the payload (text, binary, close signal..).

The second byte in the frame is for the mask bit and the payload length. The mask bit is the first bit in the second byte, and defined whether the payload is masked or not. Frames sent from the client always need to be masked, but frames sent from the server don't.
The remaining 7 bits are for the payload length. 

If the payload length is less than 125 bytes, then the payload length fits in the 7 bits on the second byte. If the payload length is more than 125 bytes but less or equal to 65535 bytes, it requests a 2 byte extension using the 7 bits on the second byte, and then uses the next 2 bytes to put the payload length on. If the payload length is more than 65535 bytes, we request a 8 byte extension and then use the following 8 bytes to put the payload length on.

If need to mask the payload, create a mask key of 4 random bytes, append it to the frame, and then for each byte of the payload, XOR it with a byte on the mask key. Then append the payload to the frame. If no mask, just append the payload directly.

#### Decoding the message

We need to check the opcode first things first to make sure it doesn't specify the close signal. Then, we check get the mask bit and the payload length. After that, if the check bit is 1, we get the mask key, otherwise we just get the payload directly. If masked, then we XOR the masked payload with the mask key to get the original payload. This is because the XOR operation has a property of A ^ B ^ B = A.

