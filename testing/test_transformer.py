import sys
sys.path.append("..")

import boto3
from testing.evaluator import eval_response
from classes.Transformer import Transformer
from classes.ApiCall import ApiCall
from classes.Resource import Resource


def produce_output(num=0):
    return {"updatedVal": num+2}

@eval_response
def test_single_output():
    t = Transformer(func=produce_output, function_args={"num": 1}, output_keys=["updatedVal"])
    t.execute()
    if not "updatedVal" in t.output:
        return False
    if t.output["updatedVal"] != 3:
        return False
    return True



def configure_bucket_args(current_args=None, region=None):
    if region != "us-east-1":
        ## update in place
        current_args["CreateBucketConfiguration"] = {
            "LocationConstraint": region
        }
    return

@eval_response
def test_other_method_arg_update(client):
    t = Transformer(
        func=configure_bucket_args,
        function_args={"current_args": "@create_bucket", "region": "us-east-2"}
    )
    a = ApiCall(
        client = client,
        method = "create_bucket",
        method_args = {"Bucket": "somebucketname"}
    )
    r = Resource(
        name = "test_bucket",
        type = "s3",
        describe_apis = (t,),
        create_apis = (a,)
    )
    if len(a.method_args.keys()) != 1:
        return False
    r.describe()
    if len(a.method_args.keys()) != 2:
        return False
    return True




def run_tests():
    client = boto3.client("s3")
    if all([
       test_single_output(),
       test_other_method_arg_update(client)
    ]):
        print("\nAll Transformer tests sucessfully passed.")
    else:
        print("\nSome Transformer tests failed")
    return