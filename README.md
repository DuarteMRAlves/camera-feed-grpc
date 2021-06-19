# Camera Feed

## Overview

This project provides an Acumos asset to provide an interface with a web camera.
It calls the camera and transmits the next image each time a request is received.


## Usage

The asset can be deployed as a docker container, by running the following command:

```shell
$ docker run --rm -p 8061:8061 \
    --env "CAMERA_URL=<host:port>" \
    --env "REQUEST_URL=/<request url>" \
    --env "USER=<user>" \
    --env "PWD=<password>" \
    sipgisr/camera-feed:latest
```

The docker container has the following environment variables:

### CAMERA_URL

```CAMERA_URL``` specifies the host and port where the camera is listenning. 
It is a mandatory parameter.

### REQUEST_URL

```REQUEST_URL``` specifies the remaining of the camera url to call for getting
images. It is also required.

### USER and PWD

```USER``` defines the user if authentication is required to access the camera.

```PWD``` defines the passowrd if authentication is required to access the camera.

These parameters should either be both defined or not. 
If only one is defined, the value will be ignored.
