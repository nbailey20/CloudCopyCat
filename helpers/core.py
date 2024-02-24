import boto3


def create_session(profile_name, region="us-east-1"):
    if region == "*":
        region = "us-east-1"
    return boto3.Session(profile_name=profile_name, region_name=region)



## Recurse through dict to return value(s) defined in expression
##   Nested dict values are declared with '/'
##     E.g. {"bucket_owner": "Owner/DisplayName"}
##   All values in list are declared with '*'
##     E.g. {"all_buckets": "Buckets/*/Name"}
##   Specific search terms for lists are declared with '?' and '~term' in next subfield
##     E.g. {"specific_bucket": "Buckets/?/Name~CloudCopyCat"}
##   Referencing value in Resource.state is declared with '$'
##     E.g. {"TopicArn": "$dest_sns_topic/arn"} - used for method_args
def get_dict_value_from_expression(dict_obj: dict, expression: list[str]):
    if not expression or not dict_obj:
        return None
    
    if len(expression) == 1:
        if expression[0] not in dict_obj:
            return None
        return dict_obj[expression[0]]

    try:
        next_key = expression[0]
        ## handle cases where api_res is a list
        if next_key == "*":
            return [get_dict_value_from_expression(key, expression[1:]) 
                    for key in dict_obj]

        elif next_key == "?":
            filter_key, filter_value = expression[1].split("~")
            filtered_res = None
            for obj in dict_obj:
                if filter_value in obj[filter_key]:
                    filtered_res = obj[filter_key]
            if len(expression) < 3:
                return filtered_res
            get_dict_value_from_expression(filtered_res, expression[2:])

        ## handle case where dict_obj is a dict
        else:
            return get_dict_value_from_expression(dict_obj[next_key], expression[1:])
    except:
        return None