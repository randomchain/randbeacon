#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <assert.h>

// can be build with gcc proxy.c -lzmq -o proxy

int main (int argc, char* argv[])
{
    int frontend_sock_t = 0;
    int backend_sock_t  = 0;
    char* frontend_addr = NULL;
    char* backend_addr  = NULL;
    if (!(argc > 1)) {
        puts("first argument must be either 'forward' or 'stream'");
        exit(1);
    } else {
        if (strcmp("forward", argv[1]) == 0) {
            frontend_sock_t = ZMQ_XSUB;
            backend_sock_t = ZMQ_XPUB;
            puts("Forwarder selected");
        } else if (strcmp("stream", argv[1]) == 0) {
            frontend_sock_t = ZMQ_PULL;
            backend_sock_t = ZMQ_PUSH;
            puts("Streamer selected");
        } else {
            puts("Unknown proxy type... only 'forward' or 'stream' allowed");
            exit(1);
        }
    }
    if (argc == 4) {
        frontend_addr = argv[2];
        backend_addr  = argv[3];
    } else {
        frontend_addr = "tcp://*:5555";
        backend_addr  = "tcp://*:6666";
    }

    void *context = zmq_ctx_new ();

    void *frontend = zmq_socket(context, frontend_sock_t);
    int rc = zmq_bind(frontend, frontend_addr);
    printf("Frontend -> %s\n", frontend_addr);
    assert(rc == 0);

    void *backend = zmq_socket(context, backend_sock_t);
    rc = zmq_bind(backend, backend_addr);
    printf("Backend -> %s\n", backend_addr);
    assert(rc == 0);

    //  Run the proxy until the user interrupts us
    puts("Starting proxy...");
    zmq_proxy(frontend, backend, NULL);

    zmq_close(frontend);
    zmq_close(backend);
    zmq_ctx_destroy(context);
    return 0;
}

