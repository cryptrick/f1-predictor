import logging

from rq import Queue, Worker

from app.db import init_db
from app.queue import redis_conn

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")


def main() -> None:
    init_db()
    Worker([Queue("default", connection=redis_conn)], connection=redis_conn).work(with_scheduler=False)


if __name__ == "__main__":
    main()
