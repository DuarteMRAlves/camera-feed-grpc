import grpc
import grpc_reflection.v1alpha.reflection as grpc_reflect
import logging
import os

from base64 import b64encode
from concurrent import futures
from http import HTTPStatus
from http.client import HTTPConnection

from feed_pb2 import Image, DESCRIPTOR as feed_descriptor
from feed_pb2_grpc import (
    ImageFeedServiceServicer,
    add_ImageFeedServiceServicer_to_server
)

_PORT_ENV_VARIABLE = 'PORT'
_DEFAULT_PORT = 8061

_SERVICE_NAME = 'ImageFeedService'
_URL_ENV_VARIABLE = 'CAMERA_URL'
_REQUEST_URL_ENV_VARIABLE = 'REQUEST_URL'


class Server(ImageFeedServiceServicer):

    def __init__(self, connection_url, request_url, user, password):
        self.__connection = HTTPConnection(connection_url)
        self.__request_url = request_url

        user_and_pass = b64encode(
            f'{user}:{password}'.encode('utf-8')
        ).decode("ascii")

        self.__headers = {
            'Accept': 'image/webp,image/png,image/svg+xml,image/*;q=0.8,video/*;q=0.8,*/*;q=0.5',
            'Connection': 'keep-alive',
            'Accept-Encoding': 'gzip, deflate',
            'Authorization': f'Basic {user_and_pass}'
        }

    def Get(self, request, context):
        self.__connection.request("GET", self.__request_url, headers=self.__headers)
        response = self.__connection.getresponse()
        if response.status != HTTPStatus.OK:
            logging.critical("Received response with status %s", response.status)
            exit(1)
        img_bytes = response.read()
        return Image(data=img_bytes)


def main():
    connection_url = os.getenv(_URL_ENV_VARIABLE)
    if not connection_url:
        logging.critical(
            "Unable to find camera url: Set the %s environment variable.",
            _URL_ENV_VARIABLE)
        exit(1)
    request_url = os.getenv(_REQUEST_URL_ENV_VARIABLE)
    if not request_url:
        logging.critical(
            "Unable to find request url: Set the %s environment variable.",
            _REQUEST_URL_ENV_VARIABLE)
        exit(1)
    logging.info(
        'Connected to \'%s\' with request url \'%s\'',
        connection_url,
        request_url
    )
    user = 'admin'
    password = 'admin'
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