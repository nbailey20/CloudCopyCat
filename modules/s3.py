import json

from modules.sts import get_account_id


## Returns dict of region str => bucket name list
## If region != "*", only key in dict is region
def get_buckets(session, region):
    account_id = get_account_id(session=session)
    client = session.client("s3")
    bucket_names = [b["Name"] for b in client.list_buckets()["Buckets"]]

    bucket_region_dict = {}
    for bucket_name in bucket_names:
        bucket_region = client.get_bucket_location(
            Bucket              = bucket_name,
            ExpectedBucketOwner = account_id
        )["LocationConstraint"]
        if not bucket_region:
            ## buckets in east1 have null LocationConstraint value
            ## https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_bucket_location.html
            bucket_region = "us-east-1"

        if bucket_region not in bucket_region_dict:
            bucket_region_dict[bucket_region] = [bucket_name]
        else:
            bucket_region_dict[bucket_region].append(bucket_name)

    if region != "*":
        return {region: bucket_region_dict[region]}
    return bucket_region_dict



def create_bucket(session, region, kms_id, bucket_name):
    account_id = get_account_id(session=session)
    client = session.client("s3")

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
                        "KMSMasterKeyID": kms_id
                    }
                }
            ]
        },
        ExpectedBucketOwner = account_id
    )
    client.put_bucket_notification_configuration(
        Bucket = bucket_name,
        NotificationConfiguration = {
            "EventBridgeConfiguration": {}
        }
    )
    client.put_bucket_versioning(
        Bucket = bucket_name,
        VersioningConfiguration = {
            "MFADelete": "Disabled",
            "Status": "Enabled"
        }
    )
    return


def get_bucket_policy(session, bucket_name):
    client = session.client("s3")
    policy = json.loads(client.get_bucket_policy(
        Bucket = bucket_name
    )["Policy"])
    return policy


def generate_src_bucket_policies(session, src_buckets, batch_role_arn):
    from resources.s3.source_bucket import SOURCE_BUCKET_POLICY_TEMPLATE

    policies = []
    src_arns = [f"arn:aws:s3:::{b}/*" for b in src_buckets]

    for idx, bucket in enumerate(src_buckets):
        ## don't overwrite existing bucket policies
        ## add an additional statement
        policy = get_bucket_policy(session, bucket)
        statements = policy["Statement"]
        SOURCE_BUCKET_POLICY_TEMPLATE["Principal"]["AWS"] = [batch_role_arn]
        SOURCE_BUCKET_POLICY_TEMPLATE["Resource"] = [src_arns[idx]]
        statements.append(
            SOURCE_BUCKET_POLICY_TEMPLATE
        )
        policies.append(json.dumps(policy))
    return policies


def generate_dest_bucket_policy(src_buckets, src_account_id, dest_bucket_name):
    from resources.s3.dest_bucket import DEST_BUCKET_POLICY_TEMPLATE

    src_arns = [f"arn:aws:s3:::{b}" for b in src_buckets]
    statement = DEST_BUCKET_POLICY_TEMPLATE["Statement"][0]
    statement["Resource"] = f"arn:aws:s3:::{dest_bucket_name}/*"
    statement["Condition"]["ArnLike"]["aws:SourceArn"] = src_arns
    statement["Condition"]["StringEquals"]["aws:SourceAccount"] = src_account_id
    return json.dumps(DEST_BUCKET_POLICY_TEMPLATE)


def add_bucket_policies(src_session, dest_session, src_buckets, src_account_id, dest_bucket_name, batch_role_arn):
    dest_bucket_policy = generate_dest_bucket_policy(src_buckets, src_account_id, dest_bucket_name)
    client = dest_session.client("s3")
    client.put_bucket_policy(
        Bucket = dest_bucket_name,
        Policy = dest_bucket_policy
    )

    src_bucket_policies = generate_src_bucket_policies(src_session, src_buckets, batch_role_arn)
    client = src_session.client("s3")
    for idx, bucket in enumerate(src_buckets):
        client.put_bucket_policy(
            Bucket = bucket,
            Policy = src_bucket_policies[idx]
        )
    return


def create_s3_object(session, bucket_name, key, filename=None, data=None):
    client = session.client("s3")
    if filename:
        client.upload_file(
            Bucket   = bucket_name,
            Filename = f"resources/lambda/{filename}",
            Key      = key
        )
    
    elif data:
        client.put_object(
            Body   = bytes(json.dumps(data)),
            Bucket = bucket_name,
            Key    = key
        )
    return


def create_state_object(session, src_buckets, dest_bucket_name):
    from helpers.config import LAMBDA_STATE_FILE_NAME
    from resources.s3.dest_bucket import STATE_FILE_SCHEMA as state

    state["awaiting_inv_report"] = src_buckets
    create_s3_object(session, dest_bucket_name, LAMBDA_STATE_FILE_NAME, data=state)
    return


def create_inv_configs(session, src_buckets, dest_account_id, dest_bucket_name):
    from helpers.config import INV_REPORT_CONFIG_ID
    client = session.client("s3")

    for src_bucket in src_buckets[:1]: ## limit for testing
        print(f"Adding inv config to {src_bucket}")
        client.put_bucket_inventory_configuration(
            Bucket = src_bucket,
            Id     = INV_REPORT_CONFIG_ID,
            InventoryConfiguration = {
                "Destination": {
                    "S3BucketDestination": {
                        "AccountId": dest_account_id,
                        "Bucket": f"arn:aws:s3:::{dest_bucket_name}",
                        "Format": "CSV",
                        "Prefix": "CloudCopyCat-Data"

                    }
                },
                "IsEnabled": True,
                "Id": INV_REPORT_CONFIG_ID,
                "IncludedObjectVersions": "All",
                "Schedule": {
                    "Frequency": "Daily"
                }
            }
        )
    return


def delete_inv_configs(session, buckets):
    from helpers.config import INV_REPORT_CONFIG_ID
    client = session.client("s3")

    for bucket in buckets: ## limit for testing
        client.delete_bucket_inventory_configuration(
            Bucket = bucket,
            Id     = INV_REPORT_CONFIG_ID
        )
    return


def delete_bucket(session, bucket_name):
# NEED to make sure bucket is empty first
    account_id = session.client("sts").get_caller_identity()["Account"]
    client = session.client("s3")
    client.delete_bucket(
        Bucket              = bucket_name,
        ExpectedBucketOwner = account_id
    )
    return