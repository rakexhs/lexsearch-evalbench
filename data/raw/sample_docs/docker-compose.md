# Multi-container Apps with Docker Compose

<!-- category: containers -->

## What it does
Docker Compose defines and runs multi-container applications using a single YAML
file, typically `docker-compose.yml`. Each service is described under the `services`
key with its image or build context, ports, environment variables, and volumes.

## Networking
Compose creates a default network for the application, and every service is
reachable from the others by its service name as a hostname. This means a web
service can connect to a database service simply by using the database's service
name as the host.

## Commands
`docker compose up` builds, creates, and starts all services; add `-d` to run in
detached mode. `docker compose down` stops and removes containers, networks, and the
default resources it created.
