import sys
sys.path.append("..")

import boto3
from testing.evaluator import eval_response
from classes.ApiCall import ApiCall
from classes.Resource import Resource

@eval_response
def test_no_client(name):
    r = Resource(name, "sns")
    r.create()
    r.describe()
    r.delete()
    if r.name in r.state and "arn" in r.state[r.name] and r.state[r.name]["arn"] == None:
        return True
    return False

@eval_response
def test_no_apis(client, name):
    r = Resource(name, "sns", client=client)
    r.create()
    r.describe()
    r.delete()
    if r.name in r.state and "arn" in r.state[r.name] and r.state[r.name]["arn"] == None:
        return True
    return False


@eval_response
def test_single_api_create(client, name):
    a = ApiCall(
            client,
            method = "create_topic",
            method_args = {"Name": "test-ccc-topic"},
            output_keys = {"arn": "TopicArn"}
        )
    r = Resource(name, type="sns", client=client, create_apis=(a,))
    r.create()
    if r.name in r.state and "arn" in r.state[r.name] and r.state[r.name]["arn"].startswith("arn:aws:sns:"):
        return True
    return False


@eval_response
def test_describe(client, name):
    a = ApiCall(
            client,
            method = "list_topics",
            output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topic/TopicArn"}
        )
    r = Resource(name, type="sns", client=client, describe_apis=(a,))
    r.describe()
    if r.name in r.state and "arn" in r.state[r.name] and r.state[r.name]["arn"].startswith("arn:aws:sns:"):
        return True
    return False


@eval_response
def test_single_api_delete(client, name):
    aList = ApiCall(
            client,
            method = "list_topics",
            output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topic/TopicArn"}
        )
    aList.execute()
    topic_arn = aList.output["arn"]

    aDelete = ApiCall(
            client,
            method = "delete_topic",
            method_args = {"TopicArn": topic_arn},
        )
    r = Resource(name, type="sns", client=client, describe_apis=(aList,), delete_apis=(aDelete,))
    r.delete()

    a = ApiCall(
            client,
            method = "list_topics",
            output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topic/TopicArn"}
        )
    a.execute()
    topic_arn = a.output["arn"]
    if r.name in r.state and "arn" in r.state[r.name] and r.state[r.name]["arn"] == None:
        return True
    return False


@eval_response
def test_complete_example_working(client, name):
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
                        method_args = {"TopicArn": f"${name}/arn"}
                    )
    display_name = ApiCall(
                        client,
                        method="set_topic_attributes",
                        method_args={
                            "AttributeName": "DisplayName",
                            "AttributeValue": "testy",
                            "TopicArn": f"${name}/arn"
                        }
                    )
    r = Resource(
            name,
            type = "sns",
            client = client, 
            create_apis = (create_topic, display_name),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,)
        )
    r.describe()
    print(r.state)
    if r.state[r.name]["arn"]:
        print(1)
        return False
    r.create()
    if not r.state[r.name]["arn"]:
        print(2)
        return False
    r.delete()
    if r.state[r.name]["arn"]:
        return False
    return True



@eval_response
def test_complete_example_broken(client, name):
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
                        method_args = {"TopicArn": f"${name}/arn"}
                    )
    display_name = ApiCall(
                        client,
                        method="set_topic_attributes",
                        method_args={
                            "AttributeName": "BadValue", ## set invalid attribute, will cause error
                            "AttributeValue": "testy",
                            "TopicArn": f"${name}/arn"
                        }
                    )
    r = Resource(
            name,
            type = "sns",
            client = client,
            create_apis = (create_topic, display_name),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,)
        )
    r.describe()
    if r.state[r.name]["arn"]:
        return False
    r.create()
    if r.state[r.name]["arn"]:
        return False
    return True


@eval_response
def test_complete_example_multiple_actions(client, name):
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
                        method_args = {"TopicArn": f"${name}/arn"}
                    )
    r = Resource(
            name,
            type = "sns",
            create_apis = (create_topic,),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,)
        )
    r.set_client(client)
    r.create()
    r.create() ## ensure no error happens here
    if not r.state[r.name]["arn"]:
        return False
    r.delete()
    r.delete() ## ensure no error happens here
    if r.state[r.name]["arn"]:
        return False
    return True



def run_tests():
    client = boto3.client("sns")
    sns_resource_name = "testSNS"
    type = "sns"
    if all([
        test_no_client(sns_resource_name),
        test_no_apis(client, sns_resource_name),
        test_single_api_create(client, sns_resource_name),
        test_describe(client, sns_resource_name),
        test_single_api_delete(client, sns_resource_name),
        # test_complete_example_working(client, sns_resource_name),
        # test_complete_example_broken(client, sns_resource_name),
        # test_complete_example_multiple_actions(client, sns_resource_name)
    ]):
        print("\nAll Resource tests sucessfully passed.")
    else:
        print("\nSome Resource tests failed")
    return