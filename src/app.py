import socket

import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import logging
import os

from base64 import b64encode
from concurrent import futures
from http import HTTPStatus
from http.client import HTTPConnection, HTTPException

from grpc_status import rpc_status
from google.rpc import code_pb2, status_pb2

from feed_pb2 import Image, DESCRIPTOR as feed_descriptor
from feed_pb2_grpc import (
    ImageFeedServiceServicer,
    add_ImageFeedServiceServicer_to_server
)

_TIMEOUT = 10

_PORT_ENV_VARIABLE = 'PORT'
_DEFAULT_PORT = 8061

_SERVICE_NAME = 'ImageFeedService'
_URL_ENV_VARIABLE = 'CAMERA_URL'
_REQUEST_URL_ENV_VARIABLE = 'REQUEST_URL'
_USER_ENV_VARIABLE = 'USER'
_PASS_ENV_VARIABLE = 'PWD'


class Server(ImageFeedServiceServicer):

    def __init__(self, connection_url, request_url, user, password):
        self.__connection = HTTPConnection(connection_url, timeout=_TIMEOUT)
        self.__request_url = request_url

        self.__headers = {
            'Accept': 'image/webp,image/png,image/svg+xml,image/*;'
                      'q=0.8,video/*;q=0.8,*/*;q=0.5',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
        }

        if user and password:
            user_and_pass = b64encode(
                f'{user}:{password}'.encode('utf-8')
            ).decode("ascii")
            self.__headers['Authorization'] = f'Basic {user_and_pass}'

    def Get(self, request, context):
        try:
            self.__connection.request(
                "GET",
                self.__request_url,
                headers=self.__headers)
            response = self.__connection.getresponse()
        except (socket.timeout, HTTPException) as ex:
            logging.warning(
                "Exception while getting image from camera feed: %s",
                ex,
                exc_info=True)
            context.abort_with_status(rpc_status.to_status(
                status_pb2.Status(
                    code=code_pb2.UNAVAILABLE,
                    message=f"Exception while getting image from camera feed: {ex}")))

        if response.status != HTTPStatus.OK:
            logging.error("Received response with status %s", response.status)
            context.abort_with_status(rpc_status.to_status(
                status_pb2.Status(
                    code=code_pb2.CANCELLED,
                    message=f"Exception while getting image from camera feed: "
                            f"Received status code {response.status}")))
        img_bytes = response.read()
        return Image(data=img_bytes)


def find_env_variable(variable_name, required=True):
    variable = os.getenv(variable_name)
    if required and not variable:
        logging.critical(
            f'Unable to find environment variable: {variable_name}')
        exit(1)
    return variable


def main():
    connection_url = find_env_variable(_URL_ENV_VARIABLE)
    request_url = find_env_variable(_REQUEST_URL_ENV_VARIABLE)
    logging.info(
        'Connected to \'%s\' with request url \'%s\'',
        connection_url,
        request_url
    )
    user = find_env_variable(_USER_ENV_VARIABLE, required=False)
    password = find_env_variable(_PASS_ENV_VARIABLE, required=False)
    server = grpc.server(futures.ThreadPoolExecutor())
    add_ImageFeedServiceServicer_to_server(
        Server(connection_url, request_url, user, password),
        server
    )
    service_names = (
        feed_descriptor.services_by_name[_SERVICE_NAME].full_name,
        grpc_reflect.SERVICE_NAME
    )
    grpc_reflect.enable_server_reflection(service_names, server)
    port = os.getenv(_PORT_ENV_VARIABLE, _DEFAULT_PORT)
    server.add_insecure_port(f'[::]:{port}')
    logging.info('Starting server at [::]:%d', port)
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(
        format="[ %(levelname)s ] %(asctime)s (%(module)s) %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=logging.INFO)
    main()