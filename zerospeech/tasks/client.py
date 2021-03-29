import sys

import pika
import uuid


class FibonacciRpcClient:

    def __init__(self):
        self.response = None
        self.corr_id = None
        _cred = pika.credentials.PlainCredentials(username="admin", password="123")
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('0.0.0.0', credentials=_cred)
        )

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def call(self, n_value):
        self.response = ""
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=str(n_value).encode())
        while self.response == "":
            self.connection.process_data_events()
        return self.response


fibonacci_rpc = FibonacciRpcClient()


while True:
    n = input("give a number: ")
    if n == "q":
        print("quitting bye")
        break
    try:
        response = fibonacci_rpc.call(int(n))
        # print(type(response))
        print(f"=> fib({n}) = {int(response)}")
    except ValueError as e:
        print(e)
        print("Was not a number")
        continue
