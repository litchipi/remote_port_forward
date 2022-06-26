# Remote port forwarder

Pure python implementation of a remote port forwarding, for when SSH is not available.

On the receiver, get 2 listener, one for the proxy, one for the incoming port
forwarding connection

On the remote endpoint, 2 connections, one to the remote listener, one to forward
packets to the local port.

## TODO

Testing
