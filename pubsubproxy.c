#include <zmq.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>
#include <assert.h>

// can be build with gcc pubsubproxy.c -lzmq -o pubsubproxy

int main (int argc, char* argv[])
{
    char* frontend_addr = NULL;
    char* backend_addr  = NULL;
    if (argc == 3) {
        frontend_addr = argv[1];
        backend_addr  = argv[2];
    } else {
        frontend_addr = "tcp://*:5555";
        backend_addr  = "tcp://*:6666";
    }

    void *context = zmq_ctx_new ();

    //  This is where the weather server sits
    void *frontend = zmq_socket(context, ZMQ_XSUB);
    int rc = zmq_bind(frontend, frontend_addr);
    printf("Frontend -> %s\n", frontend_addr);
    assert(rc == 0);

    //  This is our public endpoint for subscribers
    void *backend = zmq_socket(context, ZMQ_XPUB);
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

