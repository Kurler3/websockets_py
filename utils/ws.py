import os

# Encode to ws_frame.


def encode_to_ws_frame(data, use_mask=True):

    # If data == 'exit' => Opcode needs to be 0x8
    if data == 'exit':
        return bytearray([0x80 | 0x8])

    # FIN (first bit) = 1 and Opcode = 1 (last bit)
    byte1 = 0x81

    frame = bytearray([byte1])

    # Encode the data to utf-8, which is going to result in a byte array
    payload = data.encode('utf-8')

    # Get the number of bytes from the utf-8 encoded data
    payload_length = len(payload)

    # If wants to use mask => 10000000 otherwise 00000000
    mask_bit = 0x80 if use_mask else 0x00

    # If the payload length is less or equal to 125, then we can just use the second byte for the payload length and the mask bit.
    if payload_length <= 125:

        frame.append(payload_length | mask_bit)

    # If payload length less than 65535 bytes then we can use 2 extra bytes
    elif payload_length <= 65535:

        frame.append(126 | mask_bit)

        # ?? Fitting the payload length into 2 bytes, because its too big to put into 1.

        #
        # Most significant byte of length
        frame.append((payload_length >> 8) & 0xFF)

        frame.append(payload_length & 0xFF)  # Least significant byte of length

    # In this case, we will need to use 8 bytes for the payload length.
    else:

        # 0x7F for 8-byte length encoding (larger payloads)
        frame.append(127 | mask_bit)

        # 8-byte encoding for lengths greater than 65535
        for i in range(8):

            # Essentially, appends a byte representing a 8 bit slot in the payload length. Starting from the left-most.
            frame.append(
                    (payload_length >> (8 * (7 - i))) & 0xFF
            )

    # If using mask
    if use_mask:

        # Generate random 4 bytes for masking
        masking_key = os.urandom(4)

        # Append the masking key to the frame
        frame.extend(masking_key)

        # Mask the payload.
        # Apply the masking key to the payload
        masked_payload = bytearray()

        for i, byte in enumerate(payload):
            masked_payload.append(byte ^ masking_key[i % 4])

        payload = masked_payload

    # Add the actual payload
    frame.extend(payload)

    # Return the frame
    return frame


# Decode ws_frame.
def decode_ws_frame(data):

    if len(data) < 2:
        raise ValueError("Incomplete frame header received")

    # Get the first 2 bytes
    byte1, byte2 = data[:2]

    # Get FIN
    # Isolate the left part of the 1st byte and shift right 7 to get the last bit.
    fin = (byte1 & 0x80) >> 7

    # Get Opcode
    opcode = (byte1 & 0x0F)  # Isolate the right part of the 1st byte

    # Check if its a close frame.
    if opcode == 0x8:
        raise ValueError('Received close frame')

    # Get the mask bit
    mask_bit = (byte2 & 0x80) >> 7

    # Payload length should be the remaining 7 bits of the 2nd byte.
    payload_length = byte2 & 0x7F

    # The offset from the beginning of the frame to the actual starting byte of the utf-8 payload
    length_offset = 2

    # If this is the case, then we need to extract the actual payload length from the next 2 bytes.
    if payload_length == 126:

        if len(data) < 4:
            raise ValueError(
                'Incomplete frame: 2-byte length extension required')

        # Move the eight bits of the third byte to the left (MSB) and then append the fourth byte's 8 bits. This effectively creates a 16-bit unsigned integer.
        payload_length = (data[2] << 8) + data[3]

        length_offset += 2

    # If this is the case, we need to extract the payload length from the next 8 bytes.
    elif payload_length == 127:

        if len(data) < 10:
                raise ValueError(
                    "Incomplete frame: 8-byte length extension required.")

        # Need to create a 64-bit unsigned integer.
        # 64-bit length in the next 8 bytes
        payload_length = (
            (data[2] << 56) | (data[3] << 48) | (data[4] << 40) |
            (data[5] << 32) | (data[6] << 24) | (data[7] << 16) |
            (data[8] << 8) | data[9]
        )

        length_offset += 8

    
    # If there was a mask => extract the mask key

    mask_key = None

    if mask_bit:
        mask_key = data[length_offset:length_offset + 4]
        length_offset += 4

    # Extract the payload.
    payload = data[length_offset:length_offset + payload_length]

    if mask_key:
        payload = bytearray([byte ^ mask_key[i % 4] for i, byte in enumerate(payload)])

    decoded_msg = payload.decode('utf-8')

    return decoded_msg