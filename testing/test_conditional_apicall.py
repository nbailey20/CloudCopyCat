import sys
sys.path.append("..")

import boto3
from testing.evaluator import eval_response
from classes.ConditionalApiCall import ConditionalApiCall

def sample_exp_func(arg=None):
    return 0

@eval_response
def test_single_api(client):
    c = ConditionalApiCall(
        client = client,
        method_options = ["create_topic"],
        method_arg_options = [{"Name": "testtopic-ccc"}],
        output_key_options = [{"arn": "TopicArn"}],
        expression_func = sample_exp_func,
        expression_args = {"arg": None}
    )
    c.eval_expression()
    if c.method != "create_topic":
        return False
    c.execute()
    if not "arn" in c.output:
        return False
    if not c.output["arn"]:
        return False
    return True


def ret_arg(arg=None):
    return arg

@eval_response
def test_multiple_api(client):
    account_id = boto3.client("sts").get_caller_identity()["Account"]
    region = client.meta.region_name
    c = ConditionalApiCall(
        client = client,
        method_options = ["create_topic", "delete_topic"],
        method_arg_options = [
            {"Name": "testtopic-ccc"},
            {"TopicArn": f"arn:aws:sns:{region}:{account_id}:testtopic-ccc"}
        ],
        output_key_options = [{"arn": "TopicArn"}, {}],
        expression_func = ret_arg,
        expression_args = {}
    )
    c.eval_expression(expression_args={"arg": 1})
    if not c.method == "delete_topic":
        return False
    c.execute()
    if c.output:
        return False
    return True


def run_tests():
    client = boto3.client("sns")
    if all([
        test_single_api(client),
        test_multiple_api(client)
    ]):
        print("\nAll ConditionalApiCall tests sucessfully passed.")
    else:
        print("\nSome tests failed for ConditionalApiCall")
    return
