import boto3


def create_session(profile_name, region="us-east-1"):
    return boto3.Session(profile_name=profile_name, region_name=region)


def get_account_id(profile_name=None, session=None):
    if profile_name:
        session = create_session(profile_name)

    account_id = session.client("sts").get_caller_identity()["Account"]
    return account_id