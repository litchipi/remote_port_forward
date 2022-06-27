#!/usr/bin/env python3

# Taken from https://github.com/git-davi/reverse-python-port-forwarder

import socket
import time
import sys
import threading
import argparse

class Listener:
    BUFFER_SIZE = 0x400

    def __init__(self, tunnel_address, rppf_address):
        try :
            print("[*] Waiting for incoming tunnel connection...")
            tunnel_socket = self.make_listening_server(tunnel_address)
            self.tunnel_conn, address  = tunnel_socket.accept()

            print("[*] Opening rppf listening service on {}...".format(rppf_address))
            self.rppf_socket = self.make_listening_server(rppf_address)
            print("-------------------- Ready --------------------")

            # start thread for incoming and outcoming traffic
            tunnel2rppf_t = threading.Thread(target=self.tunnel2rppf)
            rppf2tunnel_t = threading.Thread(target=self.rppf2tunnel)
            tunnel2rppf_t.daemon = True
            rppf2tunnel_t.daemon = True

            # rppf lock (needed when connection get restarted)
            self.rppf_conn_lock = threading.Lock()

            # start threads only after connection is initiated with rppf
            self.rppf_conn, address = self.rppf_socket.accept()

            tunnel2rppf_t.start()
            rppf2tunnel_t.start()
            
            tunnel2rppf_t.join()
            rppf2tunnel_t.join()

        except KeyboardInterrupt :
            # close sockets after SIGINT
            print('\n[*] Closing connections')
            tunnel_socket.shutdown(socket.SHUT_RDWR)
            tunnel_socket.close()
            self.rppf_socket.shutdown(socket.SHUT_RDWR)
            self.rppf_socket.close()
            print('\n[*] Stopped correctly')
            sys.exit(0)

        except Exception as e :
            print('[!] An exception occurred')
            print(e)
            print('[!] Trying to close sockets')
            tunnel_socket.shutdown(socket.SHUT_RDWR)
            tunnel_socket.close()
            self.rppf_socket.shutdown(socket.SHUT_RDWR)
            self.rppf_socket.close()
            sys.exit(1)


    def make_listening_server(self, address) :
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(address)
        server_socket.listen()

        return server_socket

    # tunnel connection should be always alive and so should never launch error
    # if tunnel connection drop you should restart the program
    def tunnel2rppf(self):
        while True :
            data = self.tunnel_conn.recv(self.BUFFER_SIZE)
            if not data :
                raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")
            
            try :
                self.rppf_conn_lock.acquire()
                self.rppf_conn.sendall(data)
                self.rppf_conn_lock.release()
            except Exception :
                raise Exception("RPPF connection has been closed")

    # rppf is listening and will accept incoming connections
    def rppf2tunnel(self):
        while True :
            while True :
                data = self.rppf_conn.recv(self.BUFFER_SIZE)
                if not data :
                    break
                try :
                    self.tunnel_conn.sendall(data)
                except Exception :
                    raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

            self.rppf_conn_lock.acquire()
            self.rppf_conn.shutdown(socket.SHUT_RDWR)
            self.rppf_conn.close()

            self.rppf_conn, address = self.rppf_socket.accept()
            self.rppf_conn_lock.release()

parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter, 
        description="Raw TCP port forwarding listener")

parser.add_argument("tunnel_address",
        metavar="thost:tport",
        type=str,
        help="Tunnel address to listen to")

parser.add_argument("serve_port",
        type=int,
        help="The port on which the tunnel serves the data")

if __name__ == "__main__":
    args = parser.parse_args()

    tunnel_hostname, tunnel_port = args.tunnel_address.split(':')
    Listener((tunnel_hostname, int(tunnel_port)), ("localhost", args.serve_port))
