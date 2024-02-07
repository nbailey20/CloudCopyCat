## Create encrypted parameters used by Lambda
def create_ssm_params(session, params, key_id):
    client = session.client("ssm")
    for param in params:
        client.put_parameter(
            Name  = param["Name"],
            Value = param["Value"],
            Type  = "SecureString",
            KeyId = key_id
        )
    return


def delete_ssm_params(session, params):
    client = session.client("ssm")
    for param in params:
        client.delete_parameter(
            Name  = param
        )
    return