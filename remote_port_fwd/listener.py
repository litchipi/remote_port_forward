#!/usr/bin/env python3

import socket

# TODO  Testing

"""
Open two listeners:
    One get the connection from remote tunnel
    Other get connection from Internet browser

    Simple passthrough
"""

class Listener:
    def __init__(self, portA, portB):
        self.portA = portA
        self.portB = portB

        self.serverA = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverB = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.serverA.bind(("localhost", portA))
            self.serverB.bind(("localhost", portB))
        except Exception as e:
            print(f"Error while creating listener: {e}")
            sys.exit(1)

    def start(self):
        self.serverA_thread = threading.Thread(
            target = self.fwd,
            args=(self.serverA, self.portB)
        )
        self.serverB_thread = threading.Thread(
            target = self.fwd,
            args=(self.serverB, self.portA)
        )
        self.serverA_thread.start()
        self.serverB_thread.start()

    def fwd(self, srv, to_port):
        srv.listen(5)
        while True:
            client_socket, addr = srv.accept()

            client_thread = threading.Thread(
                target=self.conn_handler,
                args=(client_socket, to_port)
            )
            client_thread.start()

    def conn_handler(self, client_socket, to_port):
        fwd_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        fwd_socket.connect(("localhost", to_port))
        while True:
            recv_data = self.receive_data(client_socket)
            if len(recv_data):
                fwd_socket.send(recv_data)

            fwd_data = self.receive_data(fwd_socket)
            if len(fwd_data):
                client_socket.send(fwd_data)

            if not len(recv_data) and not len(fwd_data):
                client_socket.close()
                fwd_socket.close()
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

    def join(self):
        self.serverA_thread.join()
        self.serverB_thread.join()


if __name__ == "__main__":
    listener = Listener(8080, 8081)
