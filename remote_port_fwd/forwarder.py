#!/usr/bin/env python3

import socket

# TODO      Testing

class Forwarder:
    def __init__(self, local_port, remote_ip, remote_port):
        self.local_port = local_port
        self.remote = (remote_ip, remote_port)

    def start(self):
        while True:
            fwd = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            fwd.connect(self.remote)

            try:
                self.loop(fwd)
            except KeyboardInterrupt:
                break

    def loop(self, fwd):
        local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        local.connect(("localhost", self.local_port))
        while True:
            recv_data = self.receive_data(fwd)
            if len(recv_data):
                local.send(recv_data)

            local_data = self.receive_data(local)
            if len(local_data):
                fwd.send(local_data)

            if not len(recv_data) and not len(local_data):
                local.close()
                break

    def receive_data(self, s, buffer_size=1024, timeout=2):
        buffer = b""
        s.settimeout(timeout)
        try:
            while True:
                data = connection.recv(buffer_size)
                if not data:
                    break
                buffer += data
        except Exception as e:
            pass
        return buffer

if __name__ == "__main__":
    fowarder = Forwarder(8082, "localhost", 8080)
