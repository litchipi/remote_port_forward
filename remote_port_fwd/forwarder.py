#!/usr/bin/env python3

# Taken from https://github.com/git-davi/reverse-python-port-forwarder

# flush=True    is usefull when using the script through an unstable reverse shell

import socket
import time
import sys
import threading
import argparse

class Forwarder:
    BUFFER_SIZE = 4096
    
    def __init__(self, forward_address, tunnel_address):
        self.forward_address = forward_address
        self.tunnel_address = tunnel_address

        try :
            print("[*] Creating tunnel to " + str(tunnel_address), flush=True)
            self.tunnel_socket = self.establish_connection(self.tunnel_address)

            print("[*] Opening forward connection to " + str(self.forward_address), flush=True)
            self.forward_socket = self.establish_connection(self.forward_address)
            print("-------------------- Ready --------------------", flush = True)
            

            # start thread for incoming and outcoming traffic
            tunnel2forward_t = threading.Thread(target=self.tunnel2forward)
            forward2tunnel_t = threading.Thread(target=self.forward2tunnel)
            tunnel2forward_t.daemon = True
            forward2tunnel_t.daemon = True

            # create thread lock semaphore for changes on forward socket
            self.sending_socket_lock = threading.Lock()
            self.receiving_socket_lock = threading.Lock()

            tunnel2forward_t.start()
            forward2tunnel_t.start()
            
            tunnel2forward_t.join()
            forward2tunnel_t.join()

        except KeyboardInterrupt :
            # close sockets after SIGINT
            print('\n[*] Closing connections', flush = True)
            self.tunnel_socket.shutdown(socket.SHUT_RDWR)
            self.tunnel_socket.close()
            self.forward_socket.shutdown(socket.SHUT_RDWR)
            self.forward_socket.close()
            print('\n[*] Stopped correctly', flush = True)
            sys.exit(0)

        except Exception as e :
            print('[!] An exception occurred', flush = True)
            print(e)
            print('[!] Trying to close sockets', flush = True)
            self.tunnel_socket.shutdown(socket.SHUT_RDWR)
            self.tunnel_socket.close()
            self.forward_socket.shutdown(socket.SHUT_RDWR)
            self.forward_socket.close()
            sys.exit(1)


    def establish_connection(self, address):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        while True :
            try :
                client_socket.connect(address)
                break
            except :
                time.sleep(1)

        return client_socket


    def renew_socket(self, old_socket, address) :
        old_socket.shutdown(socket.SHUT_RDWR)
        old_socket.close()
        return self.establish_connection(address)


    # tunnel connection should be always alive and so should never launch error
    # if tunnel connection drop you should restart the program
    def tunnel2forward(self) :
        while True :
            data = self.tunnel_socket.recv(self.BUFFER_SIZE)
            if not data :
                raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

            print("Tunneling {} bytes".format(len(data)), flush=True)
            try :
                self.sending_socket_lock.acquire()
                self.forward_socket.sendall(data)
                self.sending_socket_lock.release()

            except Exception :
                self.sending_socket_lock.release()

                # locking other threads
                self.receiving_socket_lock.acquire()
                self.sending_socket_lock.acquire()
                self.forward_socket = self.renew_socket(self.forward_socket, forward_address)
                self.sending_socket_lock.release()
                self.receiving_socket_lock.release()

                self.forward_socket.sendall(data)


    def forward2tunnel(self) :
        while True :
            self.receiving_socket_lock.acquire()
            data = self.forward_socket.recv(self.BUFFER_SIZE)
            self.receiving_socket_lock.release()

            if not data :
                # locking other threads
                self.receiving_socket_lock.acquire()
                self.sending_socket_lock.acquire()
                self.forward_socket = self.renew_socket(self.forward_socket, forward_address)
                self.sending_socket_lock.release()
                self.receiving_socket_lock.release()
                continue

            print("Forwarding {} bytes".format(len(data)), flush=True)
            try :
                self.tunnel_socket.sendall(data)
            except Exception as e:
                raise Exception("Tunnel has dropped, this shouldn't happen, restart RPPF.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            formatter_class=argparse.RawTextHelpFormatter, 
            description="Raw TCP port forwarding")

    parser.add_argument("tunnel_address",
            metavar="thost:tport",
            type=str,
            help="The address in which the tunnel will be connected to")

    parser.add_argument("forward_address",
            metavar="fhost:fport",
            type=str,
            help="The point to be connected to on your end")

    args = parser.parse_args()

    tunnel_hostname, tunnel_port = args.tunnel_address.split(':')
    tunnel_address = (tunnel_hostname, int(tunnel_port))

    forward_hostname, forward_port = args.forward_address.split(':')
    forward_address = (forward_hostname, int(forward_port))

    Forwarder(forward_address, tunnel_address)
