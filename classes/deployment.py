from modules.sts import get_account_id, create_session
from modules.kms.state import lookup_dest_kms, lookup_src_kms

class CloudCopyCatDeployment():

    def __init__(self, src_profile=None, dest_profile=None, dest_bucket_name=None, region=None):
        self.src_account_id = get_account_id(src_profile)
        self.dest_account_id = get_account_id(dest_profile)

    ## need to use us-east-1 to list all buckets
        src_session = create_session(src_profile)
       # src_region_dict = get_src_buckets(src_session, region)
       # num_regions = len(src_region_dict.keys())

        kms_client = session.client("kms")
        self.src_kms = lookup_src_kms(kms_client, region)
        self.dest_kms = lookup_dest_kms(kms_client, region)