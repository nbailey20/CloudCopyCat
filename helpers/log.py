import logging

logging.basicConfig(format="%(levelname)s: %(message)s")

## suppress lots of noisy logs
logging.getLogger('boto3').setLevel(logging.CRITICAL) 
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('nose').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

logger = logging.getLogger()
LOGGER_INFO = logging.INFO
LOGGER_DEBUG = logging.DEBUG