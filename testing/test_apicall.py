import sys
sys.path.append("..")

import boto3
from testing.evaluator import eval_response
from classes.ApiCall import ApiCall


@eval_response
def test_no_method(client):
    a = ApiCall(client)
    a.execute()
    out = a.output
    ## if no method passed, output should be None
    if not out:
        return True
    return False


@eval_response
def test_no_args_list_function(client):
    a = ApiCall(
            client,
            method="list_topics",
            output_keys={"all_topics": "Topics/#all/TopicArn"}
        )
    a.execute()
    out = a.output
    if "all_topics" in out:
        return True
    return False


@eval_response
def test_complete_example_single_output(client):
    a = ApiCall(
                client,
                method = "create_topic",
                method_args = {"Name": "test-ccc-topic"},
                output_keys = {"arn": "TopicArn"}
            )
    a.execute()
    out = a.output
    if "arn" in out and out["arn"].startswith("arn:aws:sns:"):
        return True
    return False


@eval_response
def test_complete_example_multiple_output(client):
    a = ApiCall(
                client,
                method="list_topics",
                output_keys={
                    "all_topics": "Topics/#all/TopicArn"
                }
            )
    a.execute()
    out = a.output
    if "all_topics" not in out:
        return False
    if len(out["all_topics"]) < 1:
        return False

    first_topic = out["all_topics"][0]
    a = ApiCall(
                client,
                method = "get_topic_attributes",
                method_args = {"TopicArn": first_topic},
                output_keys = {
                    "arn": "Attributes/TopicArn",
                    "statuscode": "ResponseMetadata/HTTPStatusCode"
                }
            )
    a.execute()
    out = a.output
    if "arn" in out and "statuscode" in out:
        return True
    return False


@eval_response
def test_complete_example_no_output(client):
    a = ApiCall(
                client,
                method="list_topics",
                output_keys={
                    "arn": "Topics/?/TopicArn~test-ccc-topic/TopicArn"
                }
            )
    a.execute()
    topic_arn = a.output["arn"]
    a = ApiCall(
                client,
                method = "delete_topic",
                method_args = {"TopicArn": topic_arn}
            )
    a.execute()
    out = a.output
    if out == None and not a.exception:
        return True
    return False





def run_tests():
    client = boto3.client("sns")
    if all([
        test_no_method(client),
        test_no_args_list_function(client),
        test_complete_example_single_output(client),
        test_complete_example_multiple_output(client),
        test_complete_example_no_output(client)
    ]):
        print("\nAll ApiCall tests sucessfully passed.")
    else:
        print("\nSome tests failed for ApiCall")
    return

