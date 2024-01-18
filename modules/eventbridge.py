import json

from helpers.config import EVENTBRIDGE_RULE_NAME, EVENTBRIDGE_RULE_TARGETID, LAMBDA_FUNCTION_NAME
from resources.eventbridge.rule import EVENT_PATTERN_TEMPLATE


def generate_event_pattern(bucket_name):
    EVENT_PATTERN_TEMPLATE["detail"]["bucket"]["name"] = [bucket_name]
    return json.dumps(EVENT_PATTERN_TEMPLATE)


def create_eb_rule(session, lambda_arn, bucket_name):
    client = session.client("events")

    rule_arn = client.put_rule(
        Name         = EVENTBRIDGE_RULE_NAME,
        EventPattern = generate_event_pattern(bucket_name),
        State        = "ENABLED"
    )["RuleArn"]

    client.put_targets(
        Rule = EVENTBRIDGE_RULE_NAME,
        Targets = [
            {
                "Id": EVENTBRIDGE_RULE_TARGETID,
                "Arn": lambda_arn
            }
        ]
    )

    return rule_arn




def delete_eb_rule(session):
    client = session.client("events")

    failed_entries = client.remove_targets(
        Rule = EVENTBRIDGE_RULE_NAME,
        Ids  = [EVENTBRIDGE_RULE_TARGETID]
    )

    # if failed_entries["FailedEntryCount"] != 0:
    #     print(failed_entries[0])
    print(failed_entries)

    client.delete_rule(
        Name = EVENTBRIDGE_RULE_NAME
    )
    return