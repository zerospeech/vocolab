import time

import pika

creds = pika.credentials.PlainCredentials(username="admin", password="123")

connection = pika.BlockingConnection(pika.ConnectionParameters('0.0.0.0', credentials=creds))
channel = connection.channel()
channel.queue_declare(queue='rpc_queue')


def fib(n):
    if n <= 1:
        return n
    else:
        return fib(n - 1) + fib(n - 2)


def on_request(ch, method, props, body):
    n = int(body)

    print(f"=> fib({n})")
    response = fib(n)
    time.sleep(1)
    print(f"=> found {response}")

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(
                         correlation_id=props.correlation_id),
                     body=str(response)
                     )
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print("=> Awaiting RPC requests")
channel.start_consuming()
