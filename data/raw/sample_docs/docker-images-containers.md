# Docker Images vs Containers

<!-- category: containers -->

## Images
A Docker image is a read-only template that contains the application code, runtime,
libraries, and dependencies. Images are built in layers; each instruction in a
Dockerfile creates a new layer, and identical layers are cached and shared between
images to save space.

## Containers
A container is a running instance of an image. It adds a thin writable layer on top
of the immutable image layers. Multiple containers can run from the same image, each
isolated with its own filesystem, network interface, and process space.

## Lifecycle
`docker run <image>` creates and starts a container from an image. `docker ps`
lists running containers, and `docker ps -a` includes stopped ones. `docker stop`
sends SIGTERM to gracefully stop a container, while `docker rm` removes a stopped
container.
