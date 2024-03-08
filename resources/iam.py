import json
from classes.ApiCall import ApiCall
from classes.Resource import Resource
from classes.Transformer import Transformer
from helpers.config import LAMBDA_ROLE_NAME, LAMBDA_POLICY_NAME
from configs.iam.lambda_role import LAMBDA_IAM_POLICY_TEMPLATE, LAMBDA_TRUST_POLICY
from helpers.config import BATCH_COPY_ROLE_NAME, BATCH_COPY_POLICY_NAME
from configs.iam.batch_copy_role import BATCH_COPY_IAM_POLICY_TEMPLATE, BATCH_COPY_TRUST_POLICY
from helpers.config import REPLICATION_ROLE_NAME, REPLICATION_POLICY_NAME
from configs.iam.replication_role import REPLICATION_IAM_POLICY_TEMPLATE, REPLICATION_TRUST_POLICY


def create_role(resource_name, role_name, trust_policy):
    create = ApiCall(
                method = "create_role",
                method_args = {"RoleName": role_name, "AssumeRolePolicyDocument": json.dumps(trust_policy)},
                output_keys = {"arn": "Role/Arn"}
            )
    describe = ApiCall(
                method = "list_roles",
                output_keys = {"arn": f"Roles/?/RoleName~{role_name}/Arn"}
            )
    delete = ApiCall(
                method = "delete_role",
                method_args = {"RoleName": role_name}
            )
    role_resource = Resource(
        name = resource_name,
        type = "iam",
        create_apis = (create,),
        describe_apis = (describe,),
        delete_apis = (delete,)
    )
    return role_resource


def create_policy(resource_name, policy_name, policy_document, role_name):
    def remove_empty_valued_statements(policy=None):
        policy = json.loads(policy)
        statements = policy["Statement"]
        idx = 0
        while idx < len(statements):
            for key in statements[idx]:
                if not statements[idx][key]:
                    del statements[idx]
                    continue ## don't increment idx if we remove a statement
            idx += 1
        return {"policy": json.dumps(policy)}
    configure = Transformer(
        func = remove_empty_valued_statements,
        function_args = {"policy": json.dumps(policy_document)},
        output_keys = ["policy"]
    )
    create = ApiCall(
                method = "create_policy",
                method_args = {"PolicyName": policy_name, "PolicyDocument": f"${resource_name}/policy"},
                output_keys = {"arn": "Policy/Arn"}
            )
    attach = ApiCall(
                method = "attach_role_policy",
                method_args = {"RoleName": role_name, "PolicyArn": f"${resource_name}/arn"}
            )
    describe = ApiCall(
                method = "list_policies",
                method_args = {"Scope": "Local"},
                output_keys = {"arn": f"Policies/?/PolicyName~{policy_name}/Arn"}
            )
    detach = ApiCall(
                method = "detach_role_policy",
                method_args = {"RoleName": role_name, "PolicyArn": f"${resource_name}/arn"}
            )
    delete = ApiCall(
                method = "delete_policy",
                method_args = {"PolicyArn": f"${resource_name}/arn"}
            )
    policy_resource = Resource(
        name = resource_name,
        type = "iam",
        create_apis = (configure, create, attach),
        describe_apis = (describe,),
        delete_apis = (detach, delete)
    )
    return policy_resource



def dest_lambda_role():
    return create_role(
        "dest_lambda_role", 
        LAMBDA_ROLE_NAME,
        LAMBDA_TRUST_POLICY
        )

def dest_copy_role():
    return create_role(
        "dest_copy_role",
        BATCH_COPY_ROLE_NAME,
        BATCH_COPY_TRUST_POLICY
    )

def src_replication_role():
    return create_role(
        "src_replication_role",
        REPLICATION_ROLE_NAME,
        REPLICATION_TRUST_POLICY
    )

def dest_lambda_policy():
    return create_policy(
        "dest_lambda_policy",
        LAMBDA_POLICY_NAME,
        LAMBDA_IAM_POLICY_TEMPLATE,
        LAMBDA_ROLE_NAME
    )

def dest_copy_policy():
    return create_policy(
        "dest_copy_policy",
        BATCH_COPY_POLICY_NAME,
        BATCH_COPY_IAM_POLICY_TEMPLATE,
        BATCH_COPY_ROLE_NAME
    )

def src_replication_policy():
    return create_policy(
        "src_replication_policy",
        REPLICATION_POLICY_NAME,
        REPLICATION_IAM_POLICY_TEMPLATE,
        REPLICATION_ROLE_NAME
    )
