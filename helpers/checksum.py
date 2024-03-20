import hashlib

def generate_resource_suffix(region: str, dest_bucket_name: str, src_account__id: str, dest_account_id: str):
    s = region + dest_bucket_name + src_account__id + dest_account_id
    ## https://stackoverflow.com/a/42089311
    ## create 6-character hash of parameters that make a deployment "unique"
    return int(hashlib.sha256(s.encode("utf-8")).hexdigest(), 16) % 10**6
