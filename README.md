# Remote port forwarder

Pure python implementation of a remote port forwarding, for when SSH is not available.

On the receiver, get 2 listener, one for the proxy, one for the incoming port
forwarding connection

On the remote endpoint, 2 connections, one to the remote listener, one to forward
packets to the local port.

Taken from [git-davi's repo](https://github.com/git-davi/reverse-python-port-forwarder).

## Example

Serve a Python server in your localhost like so:
```
python3 -m http.server 8080
```

Then create a listener that get the tunnel on port `8081` and serve it on port `8082`
```
./remote_port_fwd/listener.py 8081 8082
```

Finally, create a remote port foward between the port `8080` and the port `8081`
of localhost.
```
./remote_port_fwd/forwarder.py 8081 localhost:8081
```

In your browser, you can now access the website with the URL `http://localhost:8082`.
