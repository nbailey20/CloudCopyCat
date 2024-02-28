import boto3


def create_session(profile_name, region="us-east-1"):
    if region == "*":
        region = "us-east-1"
    return boto3.Session(profile_name=profile_name, region_name=region)



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
            if filter_value in obj[filter_key]:
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
                print(f"Could not handle expression term {next_key}")
                return None
            return get_value_from_expression(dict_obj[list_idx], expression[1:])

    ## handle case where dict_obj keys are dicts
    return get_value_from_expression(dict_obj[next_key], expression[1:])