import logging

def configure_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    
    # Измените эту строку для нового формата
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - : %(message)s', datefmt='%H:%M:%S')
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

logger = configure_logger()
