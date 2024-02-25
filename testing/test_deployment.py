import sys
sys.path.append("..")

import json
from testing.evaluator import eval_response
from classes.ApiCall import ApiCall
from classes.Resource import Resource
from classes.Deployment import Deployment


@eval_response
def test_no_resources():
    d = Deployment(regions=["us-east-1"])
    d.create()
    out = d.state
    if len(out.keys()) != 2 or not "us-east-1" in out or not "iam" in out:
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
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topic/TopicArn"}
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
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topicA/TopicArn"}
                    )
    describe_topicB = ApiCall(
                        method = "list_topics",
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topicB/TopicArn"}
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



@eval_response
def test_multiple_resources_with_deps(profile):
    iam_policy = json.dumps({
        "Version": "2012-10-17",
        "Id": "key-default-1",
        "Statement": [
            {
                "Sid": "testSns",
                "Effect": "Allow",
                "Action": "sns:*",
                "Resource": "$src_snstest/arn"
            }
        ]
    })
    trust_policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    })
    role_name = "test-ccc-role"
    policy_name = "test-ccc-policy"
    iam_role_create = ApiCall(
                method = "create_role",
                method_args = {"RoleName": role_name, "AssumeRolePolicyDocument": trust_policy},
                output_keys = {"arn": "Role/Arn"}
            )
    iam_role_describe = ApiCall(
                method = "list_roles",
                output_keys = {"arn": f"Roles/?/RoleName~{role_name}/Arn"}
            )
    iam_role_delete = ApiCall(
                method = "delete_role",
                method_args = {"RoleName": role_name}
            )

    iam_policy_create = ApiCall(
                method = "create_policy",
                method_args = {"PolicyName": policy_name, "PolicyDocument": iam_policy},
                output_keys = {"arn": "Policy/Arn"}
            )
    iam_policy_attach = ApiCall(
                method = "attach_role_policy",
                method_args = {"RoleName": role_name, "PolicyArn": "$src_iam_policy/arn"}
            )
    iam_policy_describe = ApiCall(
                method = "list_policies",
                method_args = {"Scope": "Local"},
                output_keys = {"arn": f"Policies/?/PolicyName~{policy_name}/Arn"}
            )
    iam_policy_detach = ApiCall(
                method = "detach_role_policy",
                method_args = {"RoleName": role_name, "PolicyArn": "$src_iam_policy/arn"}
            )
    iam_policy_delete = ApiCall(
                method = "delete_policy",
                method_args = {"PolicyArn": "$src_iam_policy/arn"}
            )

    create_topic = ApiCall(
                method = "create_topic",
                method_args = {"Name": "test-ccc-topicA"},
                output_keys = {"arn": "TopicArn"}
            )
    describe_topic = ApiCall(
                        method = "list_topics",
                        output_keys = {"arn": "Topics/?/TopicArn~test-ccc-topicA"}
                    )
    delete_topic = ApiCall(
                        method = "delete_topic",
                        method_args = {"TopicArn": "$src_snstest/arn"}
                    )
    iam_role = Resource(
            "src_iam_role",
            type = "iam",
            create_apis = (iam_role_create,),
            describe_apis = (iam_role_describe,),
            delete_apis = (iam_role_delete,)
        )
    iam_policy = Resource(
            "src_iam_policy",
            type = "iam",
            create_apis = (iam_policy_create, iam_policy_attach),
            describe_apis = (iam_policy_describe,),
            delete_apis = (iam_policy_detach, iam_policy_delete)
        )
    sns_topic = Resource(
            "src_snstest",
            type = "sns",
            create_apis = (create_topic,),
            describe_apis = (describe_topic,),
            delete_apis = (delete_topic,)
        )
    d = Deployment(
        src_profile=profile,
        regions=["us-east-1", "us-east-2"],
        resources=(sns_topic, iam_role, iam_policy),
        dependencies={
            "src_iam_policy": ["src_snstest", "src_iam_role"]
        })
    d.create()
    if not "us-east-1" in d.state or not "us-east-2" in d.state:
        return False
    if not d.state["us-east-1"]["src_snstest"]["arn"]:
        return False
    if not d.state["iam"]["src_iam_policy"]["arn"]:
        return False
    if not d.state["iam"]["src_iam_role"]["arn"]:
        return False
    if not d.state["us-east-2"]["src_snstest"]["arn"]:
        return False
    d.delete()
    if d.state["us-east-1"]["src_snstest"]["arn"] or d.state["us-east-2"]["src_snstest"]["arn"]:
        return False
    if d.state["iam"]["src_iam_policy"]["arn"]:
        return False
    if d.state["iam"]["src_iam_role"]["arn"]:
        return False
    return True


def run_tests():
    profile = "default"
    name = "src_snsResourceTest"
    if all([
        test_no_resources(),
        test_single_resource(profile, name),
        test_multiple_resources(profile, name),
        test_multiple_resources_with_deps(profile)
    ]):
        print("\nAll Deployment tests sucessfully passed.")
    else:
        print("\nSome Deployment tests failed")
    return