import logging

log = logging.getLogger()


def set_logger():
    log.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(process)d-%(threadName)s - %(filename)20s[line:%(lineno)3d] - %(levelname)5s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)


set_logger()
