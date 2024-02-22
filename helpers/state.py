## Deployment state schema
## Policy fields are only populated if resource status is incomplete

state = {
    "src_kms": {
        "key_arn": {
            "all": [],
        },
        "key_policy": {},
        "status": {
            "key_policy": {}
        }
    },
    "src_s3": {
        "bucket_arn": {
            "all": []
        },
        "status": {
            "bucket_policy": {},
            "bucket_versioning": {},
            "bucket_replication": {},
            "batch_replication": {}
        }
    },

    "dest_eventbridge": {
        "rule_arn": {},
        "status": {
            "rule": {}
        }
    },
    "dest_iam": {
        "role_arn": {},
        "policy_arn": {},
        "status": {
            "role": {
                # "complete": [],
                # "incomplete": []
            },
            "policy": {
                # "complete": [],
                # "incomplete": []
            },
            "policy_attachment": {
                # "complete": [],
                # "incomplete": []
            }
        }
    },
    "dest_kms": {
        "key_arn": {
            "all": []
        },
        "status": {
            "key": {},
            "alias": {}
        }
    },
    "dest_lambda": {
        "function_arn": {},
        "status": {
            "function": {},
            "permission": {}
        }
    },
    "dest_sns": {
        "topic_arn": {},
        "subscription_target_list": {},
        "status": {
            "topic": {},
            "subscription": {}
        }
    },
    "dest_ssm": {
        "parameter_arn": {},
        "status": {
            "parameters": {}
        }
    },
    "dest_s3": {
        "bucket_arn": {
            "all": []
        },
        "state_object_arn": {},
        "status": {
            "bucket": {},
            "bucket_policy": {},
            "state_object": {}
        }
    }
}


def get_deployment_state(args):
    for state_key in state:
        