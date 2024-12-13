

def parse_http_request(http_request):
    decoded_strs = [string.strip() for string in http_request.decode(
        'utf-8').split('\n') if string.strip() != '']

    # If didn't get any proper strings from the data, just return
    if not decoded_strs:
        raise ValueError('Invalid http request')

    # First item in the array needs to be the method, the resource and the protocol.
    request_line = decoded_strs[0]

    request_line_arr = request_line.split(' ')

    if len(request_line_arr) != 3:
        raise ValueError('Invalid http request')
    
    method, resource, protocol = request_line_arr

    if method != 'GET' and protocol != "HTTP/1.1":
        raise Exception('Invalid HTTP Request')
    
    decoded_strs = decoded_strs[1:]

    # Init dict to store all the headers.
    headers = {}

    for header_line in decoded_strs:
        header, value = header_line.split(': ')
        headers[header] = value

    return (
        method,
        resource,
        protocol,
        headers,
    )