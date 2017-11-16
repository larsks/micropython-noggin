def chunked_reader(fd, bufsize=256):
    '''Yield bufsize chunks of a file until we're done'''
    buf = bytearray(bufsize)
    while True:
        nb = fd.readinto(buf)
        if not nb:
            break
        yield buf[:nb]
