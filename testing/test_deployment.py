import sys
sys.path.append("..")

import boto3
from testing.evaluator import eval_response
from classes.ApiCall import ApiCall
from classes.Resource import Resource
from classes.Deployment import Deployment


@eval_response
def test_no_resources():
    s = Deployment(regions=["us-east-1"])
    s.create()
    out = s.state
    if len(out.keys()) != 1 or not "us-east-1" in out:
        return False
    return True


@eval_response
def test_single_resource(profile, name):
    create_topic = ApiCall(
                method = "create_topic",
                method_args = {"Name": "test-ccc-topic"},
                output_keys = {"arn": "TopicArn"}
            )
    describe_topic = ApiCall(
                        method = "list_topics",
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topic"}
                    )
    delete_topic = ApiCall(
                        method = "delete_topic",
                        method_args = {"TopicArn": f"${name}/arn"}
                    )
    r = Resource(
            name,
            type="sns",
            create_apis = (create_topic,),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,)
        )
    d = Deployment(regions=["us-east-1"], src_profile=profile, resources=(r,))
    d.create()
    if "us-east-1" not in d.state:
        return False
    if name not in d.state["us-east-1"]:
        return False
    if not d.state["us-east-1"][name]["arn"]:
        return False
    d.delete()
    if d.state["us-east-1"][name]["arn"]:
        return False
    return True


@eval_response
def test_multiple_resources(profile, name):
    create_topicA = ApiCall(
                method = "create_topic",
                method_args = {"Name": "test-ccc-topicA"},
                output_keys = {"arn": "TopicArn"}
            )
    create_topicB = ApiCall(
                method = "create_topic",
                method_args = {"Name": "test-ccc-topicB"},
                output_keys = {"arn": "TopicArn"}
            )
    describe_topicA = ApiCall(
                        method = "list_topics",
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topicA"}
                    )
    describe_topicB = ApiCall(
                        method = "list_topics",
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topicB"}
                    )
    delete_topicA = ApiCall(
                        method = "delete_topic",
                        method_args = {"TopicArn": f"${name+'A'}/arn"}
                    )
    delete_topicB = ApiCall(
                        method = "delete_topic",
                        method_args = {"TopicArn": f"${name+'B'}/arn"}
                    )
    rA = Resource(
            name+"A",
            type = "sns",
            create_apis = (create_topicA,),
            describe_apis = (describe_topicA,),
            delete_apis = (delete_topicA,)
        )
    rB = Resource(
            name+"B",
            type = "sns",
            create_apis = (create_topicB,),
            describe_apis = (describe_topicB,),
            delete_apis = (delete_topicB,)
        )
    d = Deployment(src_profile=profile, regions=["us-east-1", "us-east-2"], resources=(rA, rB))
    d.create()
    if not "us-east-1" in d.state or not "us-east-2" in d.state:
        return False
    if not name+"A" in d.state["us-east-1"] or not name+"B" in d.state["us-east-1"]:
        return False
    if not name+"A" in d.state["us-east-2"] or not name+"B" in d.state["us-east-2"]:
        return False
    if not d.state["us-east-1"][name+"A"]["arn"] or not d.state["us-east-1"][name+"B"]["arn"]:
        return False
    if not d.state["us-east-2"][name+"A"]["arn"] or not d.state["us-east-2"][name+"B"]["arn"]:
        return False
    d.delete()
    if d.state["us-east-1"][name+"A"]["arn"] or d.state["us-east-2"][name+"B"]["arn"]:
        return False
    return True


def run_tests():
    profile = "default"
    name = "src_snsResourceTest"
    if all([
        test_no_resources(),
        test_single_resource(profile, name),
        test_multiple_resources(profile, name)
    ]):
        print("\nAll Deployment tests sucessfully passed.")
    else:
        print("\nSome Deployment tests failed")
    return