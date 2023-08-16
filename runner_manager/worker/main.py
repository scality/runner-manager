from rq import Queue, Worker

from runner_manager.dependencies import get_queue

if __name__ == "__main__":
    queue: Queue = get_queue()
    worker = Worker(
        queues=[queue],
        connection=queue.connection,
    )
    worker.work(with_scheduler=True)
