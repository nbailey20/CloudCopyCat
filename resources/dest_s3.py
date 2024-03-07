import json
from classes.ApiCall import ApiCall
from classes.Transformer import Transformer
from classes.Resource import Resource
from configs.s3.dest_bucket import DEST_BUCKET_POLICY_TEMPLATE, STATE_FILE_SCHEMA
from helpers.config import LAMBDA_STATE_FOLDER, LAMBDA_STATE_FILE_NAME
from helpers.config import REPLICATION_ROLE_NAME


## DEST BUCKET
def dest_bucket(bucket_name, dest_account):
    def generate_bucket_arn(name=None):
        if name == None or name == "null":
            return {"arn": None}
        return {"arn": f"arn:aws:s3:::{name}"}
    get_bucket_arn = Transformer(
        func = generate_bucket_arn,
        function_args = {"name": "$dest_bucket/name"},
        output_keys = ["arn"]
    )
    def generate_object_arn(bucket_arn=None):
        if bucket_arn == None:
            return {"object_arn": None}
        return {"object_arn": f"{bucket_arn}/*"}
    get_object_arn = Transformer(
        func = generate_object_arn,
        function_args = {"bucket_arn": "$dest_bucket/arn"},
        output_keys = ["object_arn"]
    )


    ## creation APIs
    method_args = {
        "Bucket": bucket_name
    }
    def configure_create_bucket(current_args=None, region=None):
        if region != "us-east-1":
            ## update in place
            current_args["CreateBucketConfiguration"] = {
                "LocationConstraint": region
            }
        return
    configure_create_bucket_args = Transformer(
        func = configure_create_bucket,
        function_args = {
            "current_args": "@create_bucket",
            "region": "$region"
        }
    )
    create_bucket = ApiCall(
        method      = "create_bucket",
        method_args = method_args,
        output_keys = {"name": bucket_name}
    )
    get_bucket_name = ApiCall(
        method = "list_buckets",
        output_keys = {"name": f"Buckets/?/Name~{bucket_name}/Name"}
    )
    put_encryption = ApiCall(
        method = "put_bucket_encryption",
        method_args = {
            "Bucket": bucket_name,
            "ServerSideEncryptionConfiguration": {
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "aws:kms",
                        "KMSMasterKeyID": "$dest_kms_key/arn"
                    }
                }]
            }
        }
    )
    put_notification_configuration = ApiCall(
        method = "put_bucket_notification_configuration",
        method_args = {
            "Bucket": bucket_name,
            "NotificationConfiguration": {
                "EventBridgeConfiguration": {}
            }
        }
    )
    put_versioning = ApiCall(
        method = "put_bucket_versioning",
        method_args = {
            "Bucket": bucket_name,
            "VersioningConfiguration": {
                "MFADelete": "Disabled",
                "Status": "Enabled"
            }
        }
    )
    def add_replication_role(policy=None):
        policy = json.loads(policy)
        policy["Statement"][0]["Condition"]["ArnLike"]["aws:PrincipalArn"] = f"arn:aws:iam::{dest_account}:role/{REPLICATION_ROLE_NAME}"
        return {"policy": json.dumps(policy)}
    configure_policy = Transformer(
        func = add_replication_role,
        function_args = {"policy": json.dumps(DEST_BUCKET_POLICY_TEMPLATE)},
        output_keys = ["policy"]
    )
    put_policy = ApiCall(
        method = "put_bucket_policy",
        method_args = {
            "Bucket": bucket_name,
            "Policy": "$dest_bucket/policy"
        }
    )
    put_state_object = ApiCall(
        method = "put_object",
        method_args = {
            "Bucket": bucket_name,
            "Key": f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}",
            "Body": bytes(json.dumps(STATE_FILE_SCHEMA), encoding="utf-8")
        }
    )

    ## describe APIs
    describe_bucket = ApiCall(
        method = "list_buckets",
        output_keys = {"name": f"Buckets/?/Name~{bucket_name}/Name"}
    )

    ## delete APIs
    delete_bucket = ApiCall(
        method = "delete_bucket",
        method_args = {
            "Bucket": bucket_name
        }
    )
    
    bucket_resource = Resource(
        name = "dest_bucket",
        type = "s3",
        create_apis = (
            configure_create_bucket_args,
            create_bucket,
            get_bucket_name,
            get_bucket_arn,
            get_object_arn,
            put_encryption,
            put_notification_configuration,
            put_versioning,
            configure_policy,
            put_policy,
            put_state_object
        ),
        describe_apis = (describe_bucket, get_bucket_arn, get_object_arn),
        delete_apis = (delete_bucket,)
    )

    return bucket_resource