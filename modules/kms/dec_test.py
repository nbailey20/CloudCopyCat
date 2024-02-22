import boto3
from botocore.exceptions import ClientError

def catch_client_errors(aws_api_func):
    def wrapper(*args, **kwargs):
        try:
            return aws_api_func(*args, **kwargs)
        except ClientError as err:
            print("Ran into AWS error: ", err)

    return wrapper


@catch_client_errors
def list_bucket(name):
    
    pass
