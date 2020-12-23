import multiprocessing as mp
import socket
import numpy as np
import pickle

def send(conn, data, size_type, block_size=4096):
    pickled = pickle.dumps(data)
    length = size_type(len(pickled))
    conn.sendall(len.tobytes())
    conn.sendall(pickled)

def recv(conn, size_type):
    size_length = size_type().nbytes

    length = conn.recv(size_length)
    assert len(length) == size_length
    length = np.frombuffer(length, dtype=size_type)

    data = ""
    for i in range(0, length, block_size):
        cur_block_size = min(block_size, length - i)
        data += conn.recv(cur_block_size)

    return pickle.loads(data)

def Processing(processor, port, size_type):
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    socket.bind(('0.0.0.0', port))
    socket.listen(1)

    while True:
        conn, address = socket.accept()
        params = recv(conn, size_type)
        assert type(params) == tuple

        result = processor(*params)

        send(conn, result, size_type)


class AsyncProcesor:
    def __init__(self, processor):
        self._data_queue = mp.Queue()
        self._processor = mp.Process(Processing, args=(processor, self._data_queue, np.uint64))
        self._processor.start()

    def __call__(self, data):

