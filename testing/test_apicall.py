import sys
sys.path.append("..")

import boto3
from classes.ApiCall import ApiCall

def eval_response(func):
    def wrapper(*args, **kwargs):
        print(f"\nTesting function {func.__name__}")
        res = func(*args, **kwargs)
        if res == False:
            print("Test Failed.")
        else:
            print("Test succeeded.")
        return res
    return wrapper



@eval_response
def test_no_method(client):
    a = ApiCall(client).output
    ## if no method passed, class should be None
    if not a:
        return True
    return False


@eval_response
def test_no_args_list_function(client):
    a = ApiCall(
            client,
            method="list_buckets",
            output_keys={"all_buckets": "Buckets/*/Name"}
        ).output
    if "all_buckets" in a:
        return True
    return False


@eval_response
def test_complete_example_single_output(client):
    buckets = ApiCall(
                client,
                method="list_buckets",
                output_keys={"all_buckets": "Buckets/*/Name"}
            ).output["all_buckets"]
    args = {"Bucket": buckets[0]}
    a = ApiCall(
            client,
            method="head_bucket",
            method_args=args,
            output_keys={"region": "ResponseMetadata/HTTPHeaders/x-amz-bucket-region"}
        ).output
    if "region" in a:
        return True
    return False


@eval_response
def test_complete_example_multiple_output(client):
    buckets = ApiCall(
                client,
                method="list_buckets",
                output_keys={"all_buckets": "Buckets/*/Name"}
            ).output["all_buckets"]
    args = {"Bucket": buckets[0]}
    a = ApiCall(
            client,
            method="head_bucket",
            method_args=args,
            output_keys={
                "region": "ResponseMetadata/HTTPHeaders/x-amz-bucket-region",
                "statuscode": "ResponseMetadata/HTTPStatusCode"
            }
        ).output
    if "region" in a and "statuscode" in a:
        return True
    return False





def run_tests():
    client = boto3.client("s3")
    if all([
        test_no_method(client),
        test_no_args_list_function(client),
        test_complete_example_single_output(client),
        test_complete_example_multiple_output(client)
    ]):
        print("\nAll ApiCall tests sucessfully passed.")
    return

