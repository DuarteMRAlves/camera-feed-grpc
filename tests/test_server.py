import argparse
import grpc
import io
import matplotlib.pyplot as plt

from PIL import Image

import feed_pb2
import feed_pb2_grpc


def parse_args():
    """
    Parse arguments for test setup
    Returns:
        The arguments for the test
    """
    parser = argparse.ArgumentParser(description='Test for Image Fees Service')
    parser.add_argument(
        '--target',
        metavar='target',
        default='localhost:8061',
        help='Location of the tested server (defaults to localhost:8061)')
    return parser.parse_args()


def display_image(image):
    img = Image.open(io.BytesIO(image.data))
    ax = plt.gca()
    ax.imshow(img)
    plt.show()


if __name__ == '__main__':
    args = parse_args()
    target = args.target
    with grpc.insecure_channel(target) as channel:
        estimator_stub = feed_pb2_grpc.ImageFeedServiceStub(channel)
        try:
            response = estimator_stub.Get(feed_pb2.Empty())
            display_image(response)
        except grpc.RpcError as rpc_error:
            print('An error has occurred:')
            print(f'  Error Code: {rpc_error.code()}')
            print(f'  Details: {rpc_error.details()}')