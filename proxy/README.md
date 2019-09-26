# Simple ZeroMQ Proxy

This implementation of a ØMQ proxy is inspired by code examples from the ZeroMQ book and is very rudimentary.
It can be run as a "forwarder" or "streamer". A "forwarder" is used to proxy the PUB/SUB pattern of ØMQ,
while a "streamer" will proxy as a PUSH/PULL setup. In the "streamer" configuration, the proxy will evenly/fairly 
pull messages from the frontend, and evenly distribute them to connections on the backend.

Optionally, the proxy can be configured to capture all traffic for monitoring by publishing it 
to a seperate ØMQ subscriber. An example such a subscriber, aka. "snooper" can be seen in `snooper.py`.

## Usage

```
./proxy [forward|stream] FRONTEND_ADDR_PORT BACKEND_ADDR_PORT [CAPTURE_ADDR_PORT]
```

## Build

Requires `libzmq3-dev`

Use `make` or `gcc proxy.c -lzmq -o proxy` to build the proxy

## Notes

The setup in `.tmuxp.yaml` and scripts `gopub.py`, `pullrecv.py`, and `pushspam.py` were used for throughput testing
with different configurations of the "streamer" proxy.
