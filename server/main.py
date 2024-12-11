

#?? Handshake res if ok.
# HTTP/1.1 101 Switching Protocols
# Upgrade: websocket
# Connection: Upgrade
# Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo =
# Sec-WebSocket-Protocol: chat


# 3 types of data in the frames: text (utf-8), binary and signals (no data, just triggers for events like, closing)



###################
## HANDSHAKE ######
###################

# Take Sec-WebSocket-Key from client headers and concatenate with 258EAFA5-E914-47DA-
#   95CA-C5AB0DC85B11, then take the SHA-1 hash of this and encode to base64. Return this in the handshake.