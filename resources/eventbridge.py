import json
from classes.ApiCall import ApiCall
from classes.ResourceGroup import Resource
from helpers.config import EVENTBRIDGE_RULE_NAME, EVENTBRIDGE_RULE_TARGETID
from configs.eventbridge.rule import EVENT_PATTERN_TEMPLATE


def dest_eventbridge_rule(suffix):
    eb_name = f"{EVENTBRIDGE_RULE_NAME}-{suffix}"
    eb_target_id = f"{EVENTBRIDGE_RULE_TARGETID}-{suffix}"

    ## Create APIs
    create_rule = ApiCall(
        method = "put_rule",
        method_args = {
            "Name": eb_name,
            "EventPattern": json.dumps(EVENT_PATTERN_TEMPLATE),
            "State": "ENABLED"
        },
        output_keys = {"arn": "RuleArn"}
    )
    add_targets = ApiCall(
        method = "put_targets",
        method_args = {
            "Rule": eb_name,
            "Targets": [{
                "Id": eb_target_id,
                "Arn": "$dest_lambda_function/arn"
            }]
        }
    )

    ## Describe API
    describe_rule = ApiCall(
        method = "list_rules",
        method_args = {"NamePrefix": eb_name},
        output_keys = {"arn": f"Rules/?/Name~{eb_name}/Arn"}
    )

    ## Delete API
    remove_targets = ApiCall(
        method = "remove_targets",
        method_args = {
            "Rule": eb_name,
            "Ids": [eb_target_id]
        }
    )
    delete_rule = ApiCall(
        method = "delete_rule",
        method_args = {"Name": eb_name}
    )

    rule_resource = Resource(
        name = "dest_eventbridge_rule",
        type = "events",
        create_apis = (create_rule, add_targets),
        describe_apis = (describe_rule,),
        delete_apis = (remove_targets, delete_rule)
    )
    return rule_resource