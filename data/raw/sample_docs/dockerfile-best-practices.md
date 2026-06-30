# Writing Efficient Dockerfiles

<!-- category: containers -->

## Layer caching
Order Dockerfile instructions from least to most frequently changing. Copy your
dependency manifest (for example `requirements.txt` or `package.json`) and install
dependencies before copying the rest of the source code, so that the expensive
dependency-install layer is cached and reused when only source code changes.

## Smaller images
Use a slim or alpine base image where possible, and use multi-stage builds to keep
build tools out of the final image. A `.dockerignore` file prevents unnecessary
files from being sent to the build context, speeding up builds.

## Reducing layers
Combine related `RUN` commands with `&&` to reduce the number of layers, and clean
up package manager caches in the same layer to avoid bloating the image.
