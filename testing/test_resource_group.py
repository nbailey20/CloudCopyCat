import sys
sys.path.append("..")

import boto3
from testing.evaluator import eval_response
from classes.ApiCall import ApiCall
from classes.ResourceGroup import ResourceGroup


@eval_response
def test_single_resource(client, type):
    resource_name = "test_topic"
    create_topic = ApiCall(
                client,
                method = "create_topic",
                method_args = {"Name": "test-ccc-topic"},
                output_keys = {"arn": "TopicArn"}
            )
    describe_topic = ApiCall(
                        client,
                        method = "list_topics",
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topic/TopicArn"}
                    )
    delete_topic = ApiCall(
                        client,
                        method = "delete_topic",
                        method_args = {"TopicArn": f"${resource_name}/#id/arn"}
                    )
    rg = ResourceGroup(
            resource_name,
            type = type,
            client = client, 
            create_apis = (create_topic,),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,),
            num_resources=1
        )
    rg.create()
    try:
        if len(rg.state[rg.name]) != 1:
            return False
    except:
        return False
    if not rg.state[rg.name][0]["arn"]:
        return False
    rg.delete()
    rg.describe()
    if rg.state[rg.name][0]["arn"]:
        return False
    return True


@eval_response
def test_multiple_resources(client, type):
    resource_name = "test_topic"
    create_topic = ApiCall(
                client,
                method = "create_topic",
                method_args = {"Name": f"${resource_name}/#id/name"},
                output_keys = {"arn": "TopicArn"}
            )
    describe_topic = ApiCall(
                client,
                method = "get_topic_attributes",
                method_args = {"TopicArn": f"${resource_name}/#id/arn"},
                output_keys = {"arn": "Attributes/TopicArn"}
            )
    delete_topic = ApiCall(
                        client,
                        method = "delete_topic",
                        method_args = {"TopicArn": f"${resource_name}/#id/arn"}
                    )
    rg = ResourceGroup(
            resource_name,
            type = type,
            client = client, 
            create_apis = (create_topic,),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,),
            num_resources=3,
            state={
                resource_name: [
                    {"arn": None, "name": "test-ccc-topicA"},
                    {"arn": None, "name": "test-ccc-topicB"},
                    {"arn": None, "name": "test-ccc-topicC"}
                ]
            }
        )
    rg.create()
    try:
        if len(rg.state[rg.name]) != 3:
            return False
    except:
        return False
    for i in range(3):
        if not rg.state[rg.name][i]["arn"]:
            return False
    rg.delete()
    for i in range(3):
        if rg.state[rg.name][i]["arn"]:
            return False
    return True


def run_tests():
    client = boto3.client("sns")
    type = "sns"
    if all([
        test_single_resource(client, type),
        test_multiple_resources(client, type)
    ]):
        print("\nAll ResourceGroup tests sucessfully passed.")
    else:
        print("\nSome ResourceGroup tests failed")
    return