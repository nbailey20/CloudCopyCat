import json
from classes.ApiCall import ApiCall
from classes.Transformer import Transformer
from classes.ResourceGroup import ResourceGroup

from helpers.config import REPLICATION_ROLE_NAME
from configs.s3.source_bucket import SOURCE_BUCKET_POLICY_TEMPLATE, EMPTY_BUCKET_POLICY_TEMPLATE

## SOURCE BUCKET
def src_bucket():
    def generate_bucket_arn(name=None):
        if name == "null":
            return {"arn": None}
        return {"arn": f"arn:aws:s3:::{name}"}
    get_bucket_arn = Transformer(
        func = generate_bucket_arn,
        function_args = {"name": "$src_bucket/#id/name"},
        output_keys = ["arn"]
    )

    def generate_object_arn(name=None):
        if not name:
            return {"object_arn": None}
        return {"object_arn": f"arn:aws:s3:::{name}/*"}
    get_object_arn = Transformer(
        func = generate_object_arn,
        function_args = {"name": "$src_bucket/#id/name"},
        output_keys = ["object_arn"]
    )
    set_policy = ApiCall(
        method = "put_bucket_policy",
        method_args = {
            "Bucket": "$src_bucket/#id/name",
            "Policy": "$src_bucket/#id/policy"
        }
    )

    ## Creation APIs
    def append_statements(policy=None):
        if policy == "null":
            return {"policy": EMPTY_BUCKET_POLICY_TEMPLATE}
       # policy = json.loads(policy)
        statements = policy["Statement"]
        statements.append(SOURCE_BUCKET_POLICY_TEMPLATE)
        return {"policy": json.dumps(SOURCE_BUCKET_POLICY_TEMPLATE)}
    update_policy = Transformer(
        func = append_statements,
        function_args = {"policy": "$src_bucket/#id/policy"},
        output_keys = ["policy"]
    )
    put_versioning = ApiCall(
        method = "put_bucket_versioning",
        method_args = {
            "Bucket": "$src_bucket/#id/name",
            "VersioningConfiguration": {
                "Status": "Enabled"
            }
        }
    )
    put_replication = ApiCall(
        method = "put_bucket_replication",
        method_args = {
            "Bucket": "$src_bucket/#id/name",
            "ReplicationConfiguration": {
                "Role": f"arn:aws:iam:$region:$dest_account:role/{REPLICATION_ROLE_NAME}",
                "Rules": [
                    {
                        "ID": "CloudCopyCatReplication",
                        "Priority": 10,
                        "Filter": {
                            "Prefix": ""
                        },
                        "Status": "Enabled",
                        "SourceSelectionCriteria": {
                            "SseKmsEncryptedObjects": {
                                "Status": "Enabled"
                            }
                        },
                        "Destination": {
                            "Bucket": "$dest_bucket/arn",
                            "Account": "$dest_account",
                            "AccessControlTranslation": {
                                "Owner": "Destination"
                            },
                            "EncryptionConfiguration": {
                                "ReplicaKmsKeyID": "$dest_kms_key/arn"
                            }
                        },
                        "DeleteMarkerReplication": {
                            "Status": "Disabled"
                        }
                    }
                ]
            }
        }
    )


    ## Describe APIs
    get_policy = ApiCall(
        method = "get_bucket_policy",
        method_args = {
            "Bucket": "$src_bucket/#id/name"
        },
        output_keys = {"policy": "Policy"}
    )
    def search_for_sid(policy=None):
        if policy == "null":
            return {"arn": None}
        policy = json.loads(policy)
        for statement in policy["Statement"]:
            if "CloudCopyCat" in statement["Sid"]:
                return {"arn": f"arn:aws:s3:::$src_bucket/#id/name"}
        return {"arn": None}
    validate_policy = Transformer(
        func = search_for_sid,
        function_args = {"policy": "$src_bucket/#id/policy"},
        output_keys = ["arn"]
    )


    ## Delete APIs
    def remove_statements(policy=None):
        if not policy:
            return
        policy = json.loads(policy)
        statements = policy["Statement"]
        for statement in statements:
            if "Sid" in statement and "CloudCopyCat" in statement["Sid"]:
                statements.remove(statement)
    revert_policy = Transformer(
        func = remove_statements,
        function_args = {"policy": "$src_bucket/#id/policy"}
    )


    bucket_group = ResourceGroup(
        name = "src_bucket",
        type = "s3",
        create_apis = (
            get_object_arn,
            update_policy,
            set_policy,
            put_versioning,
            put_replication,
            get_bucket_arn
        ),
        describe_apis = (get_policy, validate_policy),
        delete_apis = (revert_policy,)
    )
    return bucket_group