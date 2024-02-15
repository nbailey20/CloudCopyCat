import json, copy
from botocore.exceptions import ClientError


## Returns dict of {region => {"buckets" => bucket names list}, {"kms" => key IDs list}}
## If region == "*", dict keys are all regions containing buckets
def get_src_buckets(session, region):
    client = session.client("s3")
    bucket_names = [b["Name"] for b in client.list_buckets()["Buckets"]]
    
    region_dict = {}
    for bucket_name in bucket_names:
        bucket_region = client.get_bucket_location(
            Bucket = bucket_name
        )["LocationConstraint"]
        if not bucket_region:
            ## buckets in east1 have null LocationConstraint value
            ## https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_bucket_location.html
            bucket_region = "us-east-1"

        bucket_encryption = client.get_bucket_encryption(
            Bucket = bucket_name
        )["ServerSideEncryptionConfiguration"]["Rules"][0]["ApplyServerSideEncryptionByDefault"]

        ## ignore buckets in regions we don't care about
        if region != bucket_region and region != "*":
            continue

        ## keep track of buckets in a given region
        if bucket_region in region_dict:
            region_dict[bucket_region]["buckets"].append(bucket_name)
        else:
            region_dict[bucket_region] = {"buckets": [bucket_name], "kms": []}

        ## keep track of kms key IDs in a given region
        if bucket_encryption["SSEAlgorithm"] == "aws:kms":
            kms_arn = bucket_encryption["KMSMasterKeyID"]
            region_dict[bucket_region]["kms"].append(kms_arn)

    ## ensure we don't have duplicate kms IDs
    for region in region_dict.keys():
        region_dict[region]["kms"] = list(set(region_dict[region]["kms"]))
    return region_dict


## Enables bucket versioning for list of bucket names
def enable_bucket_versioning(session, bucket_names):
    client = session.client("s3")
    for name in bucket_names:
        client.put_bucket_versioning(
            Bucket = name,
            VersioningConfiguration = {
                "MFADelete": "Disabled",
                "Status": "Enabled"
            }
        )
    return


## Create destination bucket for copied data and CloudCopyCat config data
## Bucket is KMS encrypted, versioning enabled, events go to EventBridge default bus
def create_dest_bucket(session, kms_arn, bucket_name):
    region     = session.region_name
    client     = session.client("s3")

    ## client throws error if us-east-1 is provided as LocationConstraint
    ## https://stackoverflow.com/questions/51912072/invalidlocationconstraint-error-while-creating-s3-bucket-when-the-used-command-i
    if region == "us-east-1":
        client.create_bucket(
            Bucket = bucket_name,
        )
    else:
        client.create_bucket(
            Bucket = bucket_name,
            CreateBucketConfiguration = {
                "LocationConstraint": region
            }
        )

    client.put_bucket_encryption(
        Bucket = bucket_name,
        ServerSideEncryptionConfiguration = {
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "aws:kms",
                        "KMSMasterKeyID": kms_arn
                    }
                }
            ]
        }
    )
    client.put_bucket_notification_configuration(
        Bucket = bucket_name,
        NotificationConfiguration = {
            "EventBridgeConfiguration": {}
        }
    )
    enable_bucket_versioning(session, [bucket_name])
    return


def get_bucket_policy(session, bucket_name):
    client = session.client("s3")
    try:
        policy = json.loads(client.get_bucket_policy(
            Bucket = bucket_name
        )["Policy"])
    except ClientError as err:
        policy = {"Version": "2012-10-17", "Statement": []}
    return policy



def generate_dest_bucket_policy(src_buckets, src_account_id, dest_bucket_name, replication_role_arn):
    from resources.s3.dest_bucket import DEST_BUCKET_POLICY_TEMPLATE

    src_arns = [f"arn:aws:s3:::{b}" for b in src_buckets]
    DEST_BUCKET_POLICY_TEMPLATE["Statement"][0]["Principal"]["AWS"] = replication_role_arn
    DEST_BUCKET_POLICY_TEMPLATE["Statement"][0]["Resource"] = f"arn:aws:s3:::{dest_bucket_name}/*"
    DEST_BUCKET_POLICY_TEMPLATE["Statement"][1]["Resource"] = f"arn:aws:s3:::{dest_bucket_name}/*"
    DEST_BUCKET_POLICY_TEMPLATE["Statement"][1]["Condition"]["ArnLike"]["aws:SourceArn"] = src_arns
    DEST_BUCKET_POLICY_TEMPLATE["Statement"][1]["Condition"]["StringEquals"]["aws:SourceAccount"] = src_account_id
    return json.dumps(DEST_BUCKET_POLICY_TEMPLATE)


## Update/put bucket policies for source and destination buckets
def add_dest_bucket_policy(dest_session, src_buckets, src_account_id, dest_bucket_name, replication_role_arn):
    dest_bucket_policy = generate_dest_bucket_policy(src_buckets, src_account_id, dest_bucket_name, replication_role_arn)
    client = dest_session.client("s3")
    client.put_bucket_policy(
        Bucket = dest_bucket_name,
        Policy = dest_bucket_policy
    )
    print("Added dest bucket policy")
    return


## Append statement to existing source bucket policies to allow Batch Copy operations
## If no bucket policy exists, create new one
## If revert == True, remove statement from bucket policy
def generate_src_bucket_policies(session, src_buckets, batch_copy_role_arn, revert):
    from resources.s3.source_bucket import SOURCE_BUCKET_POLICY_TEMPLATE

    policies = []
    src_arns = [f"arn:aws:s3:::{b}/*" for b in src_buckets]

    for idx, bucket in enumerate(src_buckets):
        template = copy.deepcopy(SOURCE_BUCKET_POLICY_TEMPLATE)
        ## don't overwrite existing bucket policies
        ## add an additional statement
        policy = get_bucket_policy(session, bucket)
        statements = policy["Statement"]
        if revert:
            for statement in statements:
                if "Sid" in statement and "CloudCopyCat" in statement["Sid"]:
                    statements.remove(statement)
        else:
            template["Principal"]["AWS"] = batch_copy_role_arn
            template["Resource"] = src_arns[idx]
            statements.append(
                template
            )
        policies.append(policy)
    return policies


def update_src_bucket_policies(src_session, src_buckets, batch_copy_role_arn, revert=False):
    src_bucket_policies = generate_src_bucket_policies(src_session, src_buckets, batch_copy_role_arn, revert)
    client = src_session.client("s3")
    for idx, bucket in enumerate(src_buckets):
        if not len(src_bucket_policies[idx]["Statement"]):
            client.delete_bucket_policy(
                Bucket = bucket
            )
        else:
            client.put_bucket_policy(
                Bucket = bucket,
                Policy = json.dumps(src_bucket_policies[idx])
            )
    print("Updated source bucket policies")
    return


def create_s3_object(session, bucket_name, key, filename=None, data=None):
    client = session.client("s3")
    if filename:
        client.upload_file(
            Bucket   = bucket_name,
            Filename = filename,
            Key      = key
        )

    elif data:
        client.put_object(
            Body   = bytes(json.dumps(data), encoding="utf-8"),
            Bucket = bucket_name,
            Key    = key
        )
    return


## Create Lambda state object used to track copy completion status for all source buckets
def create_state_object(session, src_buckets, dest_bucket_name):
    from helpers.config import LAMBDA_STATE_FOLDER, LAMBDA_STATE_FILE_NAME
    from resources.s3.dest_bucket import STATE_FILE_SCHEMA as state

    dest_object = f"{LAMBDA_STATE_FOLDER}/{LAMBDA_STATE_FILE_NAME}"
    state["awaiting_inv_report"] = src_buckets
    create_s3_object(session, dest_bucket_name, dest_object, data=state)
    return


## Add inventory configurations to all source buckets,
##  with reports delivered to the destination bucket to trigger EB rule -> Lambda
def enable_s3_replication(session, src_buckets, dest_account_id, dest_bucket_name, replication_role_arn, dest_kms_arn):
    client = session.client("s3")

    for src_bucket in src_buckets:
        response = client.put_bucket_replication(
            Bucket = src_bucket,
            ReplicationConfiguration={
                "Role": replication_role_arn,
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
                            "Bucket": f"arn:aws:s3:::{dest_bucket_name}",
                            "Account": dest_account_id,
                            "AccessControlTranslation": {
                                "Owner": "Destination"
                            },
                            "EncryptionConfiguration": {
                                "ReplicaKmsKeyID": dest_kms_arn
                            }
                        },
                        "DeleteMarkerReplication": {
                            "Status": "Disabled"
                        }
                    }
                ]
            }
        )
    return


def create_batch_replication_jobs(session, src_account_id, src_buckets, dest_account_id, dest_bucket, role_arn, kms_arn):
    client = session.client("s3control")

    for src_bucket in src_buckets:
        job_id = client.create_job(
            AccountId            = src_account_id,
            ConfirmationRequired = True,
            Operation = {
                "S3ReplicateObject": {}
            },
            Report = {
                "Enabled": False
            },
            Priority = 10,
            RoleArn  = role_arn,
            ManifestGenerator = {
                "S3JobManifestGenerator": {
                    "SourceBucket": f"arn:aws:s3:::{src_bucket}",
                    "ManifestOutputLocation": {
                        "Bucket":                      f"arn:aws:s3:::{dest_bucket}",
                        "ManifestPrefix":              f"CloudCopyCat-Data/{src_bucket}/InvReport",
                        "ManifestFormat":              "S3InventoryReport_CSV_20211130",
                        "ExpectedManifestBucketOwner": dest_account_id,
                        "ManifestEncryption": {
                            "SSEKMS": {
                                "KeyId": kms_arn
                            }
                        }
                    },
                    "Filter": {
                        "EligibleForReplication": True
                    },
                    "EnableManifestOutput": True
                }
            }
        )["JobId"]
    return


def delete_replication(session, bucket_names):
    client = session.client("s3")
    for bucket in bucket_names:
        client.delete_bucket_replication(
            Bucket = bucket
        )
    return


def delete_bucket(session, bucket_name):
    # NEED to make sure bucket is empty first
    client = session.client("s3")
    client.delete_bucket(
        Bucket = bucket_name
    )
    return