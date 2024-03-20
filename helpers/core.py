import boto3
from helpers.log import logger


def create_session(profile_name, region="us-east-1"):
    if region == "*":
        region = "us-east-1"
    session = boto3.Session(profile_name=profile_name, region_name=region)
    logger.debug(f"Created boto3 session with profile {profile_name} and region {region}")
    return session

def get_account_id(profile_name):
    if not profile_name:
        return
    session = create_session(profile_name)
    account_id = session.client("sts").get_caller_identity()["Account"]
    return account_id


## Return 2 objects:
##   1. State dict, region => bucket names in region
##   2. List of all regions included in state
def get_src_state(session, region_filter=None):
    client = session.client("s3")
    bucket_names = [b["Name"] for b in client.list_buckets()["Buckets"]]

    state = {}
    regions = []
    keys_seen = []
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
        if region_filter and region_filter != bucket_region:
            continue

        logger.debug(f"Gathering information for source bucket {bucket_name}")
        bucket_data = {
            "name": bucket_name,
            "arn": f"arn:aws:s3:::{bucket_name}",
            "object_arn": f"arn:aws:s3:::{bucket_name}/*",
            "type": "s3"
        }

        ## keep track of buckets in a given region
        if bucket_region in state:
            state[bucket_region]["src_bucket"].append(bucket_data)
        else:
            regions.append(bucket_region)
            state[bucket_region] = {"src_bucket": [bucket_data], "src_kms_key": []}

        ## keep track of kms key IDs in a given region
        ## watch out for same key encrypting multiple buckets
        if bucket_encryption["SSEAlgorithm"] != "aws:kms":
            continue
        kms_arn = bucket_encryption["KMSMasterKeyID"]
        if kms_arn in keys_seen:
            continue
        kms_data = {
            "arn": kms_arn,
            "id": kms_arn.split("/")[-1],
            "type": "kms"
        }
        state[bucket_region]["src_kms_key"].append(kms_data)
        keys_seen.append(kms_arn)
    return (state, regions)



def add_ssm_params_to_state(state, param_data):
    for region in state:
        state[region]["dest_ssm_param"] = param_data


## Recurse through dict to return value(s) defined in expression
##   Nested dict values are declared with '/'
##     E.g. {"bucket_owner": "Owner/DisplayName"}
##   All values in list are declared with '#all'
##     E.g. {"all_buckets": "Buckets/#all/Name"}
##   Specific search terms for lists are declared with '?', '~term' in next subfield, and attribute to return next
##     E.g. {"specific_bucket_creation": "Buckets/?/Name~CloudCopyCat/CreationDate"}
##   Referencing resource's own values in Resource.state is declared with '$' for the service name and '#id'
##     E.g. {"TopicArn": "$dest_sns/#id/arn"}
##   If a property for all resources in a given service is desired, use '#all'
def get_value_from_expression(dict_obj: dict, expression: str):
    if not expression or not dict_obj:
        return None

    if type(expression) == str:
        expression = expression.split("/")
    if len(expression) == 1:
        if expression[0] not in dict_obj:
            return None
        return dict_obj[expression[0]]

    next_key = expression[0]
    ## handle cases where dict_obj contains a list
    if next_key == "?":
        filter_key, filter_value = expression[1].split("~")
        filtered_res = None
        for obj in dict_obj:
            if filter_key in obj and filter_value in obj[filter_key]:
                filtered_res = obj
        if len(expression) < 3:
            return filtered_res
        return get_value_from_expression(filtered_res, expression[2:])
        
    elif next_key.startswith("#"):
        if next_key == "#all":
            return [get_value_from_expression(key, expression[1:]) 
                for key in dict_obj]
        else:
            try:
                list_idx = int(next_key[1:])
            except ValueError:
                logger.debug(f"Could not handle expression term {next_key}")
                return None
            return get_value_from_expression(dict_obj[list_idx], expression[1:])

    ## handle case where dict_obj keys are dicts, recurse
    try:
        return get_value_from_expression(dict_obj[next_key], expression[1:])
    except KeyError:
        logger.debug(f"Could not find key {next_key} in object: {dict_obj.keys()}")
        return None
    except TypeError:
        logger.debug(f"Unknown type error with key {next_key} in object")
        return None