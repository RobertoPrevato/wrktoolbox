# Dockerfile
This folder contains two working Dockerfile that can be used to create a Docker image with `wrk` and `wrk2` tools.

* the image in `ubuntu` is heavier, it uses `python:3.7` image with Ubuntu
* the image in `alpine` is lighter, since it uses `python:3.7-alpine` image with Alpine

Both images are published in [Docker Hub](https://hub.docker.com/u/robertoprevato).

```bash
docker run -it robertoprevato/wrkwrk2 /bin/bash

docker run -it robertoprevato/wrkwrk2-alpine /bin/sh
```