# Persisting Data with Docker Volumes

<!-- category: containers -->

## Why volumes
A container's writable layer is removed when the container is deleted, so data
written inside the container does not persist. Volumes provide storage that lives
independently of the container lifecycle.

## Named volumes vs bind mounts
A named volume is managed by Docker and stored in a Docker-controlled location. A
bind mount maps a specific host directory into the container, which is handy for
local development where you want code changes reflected immediately.

## Usage
Create and attach a named volume with `docker run -v mydata:/var/lib/data <image>`.
List volumes with `docker volume ls` and remove unused ones with `docker volume prune`.
