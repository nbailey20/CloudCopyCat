from botocore.exceptions import ClientError
from helpers.core import get_value_from_expression

class ApiCall():
    def execute(self, args: dict[str]=None, outputs: dict[str]=None):
        try:
            method_to_call = getattr(self.client, self.method)
        except:
            print(f"Action {self.method} not known for client, skipping")
            return
        
        ## allow custom method_args for execution
        ## takes precedence over saved args
        ## used for method_args rendered at runtime
        method_args = self.method_args
        if args:
            method_args = args

        try:
            api_res = None
            if method_args:
                api_res = method_to_call(**method_args)
            else:
                api_res = method_to_call()
        except ClientError as e:
            if e.response['Error'] and e.response['Error']['Code'] in ['AccessDenied', 'AccessDeniedException']:
                self.exception = "AccessDenied"
                print(f'CloudCopyCat does not have permission to perform {self.method}, skipping: {e}')
            elif e.response['Error'] and e.response['Error']['Code'] in ['NotFoundException', 'NoSuchEntity']:
                self.exception = "NotFound"
                print(f'Resource not found exception received from AWS client: {e}')
            else:
                self.exception = "ClientError"
                print(f'AWS client error: {e}')
                print("method", self.method)
                print("method args", method_args)
            api_res = None
        except Exception as e:
            self.exception = "UnknownError"
            print(f'Unknown API error, exiting: {e}')
            print("method", self.method)
            print("method args", method_args)
            api_res = None

        self._store_outputs(api_res, outputs)
        return api_res


    def set_client(self, client):
        self.client = client

    ## Set self.output to be dict containing output_key => output_values
    def _store_outputs(self, api_res: dict[str], outputs: dict[str]=None):
        expected_output = self.expected_output
        if outputs:
            expected_output = outputs
        if not expected_output:
            return
        self.output = {}
        for key in expected_output:
            output_expression = expected_output[key]
            self.output[key] = get_value_from_expression(api_res, output_expression)


    ## Make API call to method with method_args
    ## Outputs dict determines which values from API response are returned
    ##  {name of output => path in API response where value is found}
    ##   Nested JSON values are declared with '/'
    ##     E.g. {"bucket_owner": "Owner/DisplayName"}
    ##   All values in list are declared with '*'
    ##     E.g. {"all_buckets": "Buckets/*/Name"}
    ##   Specific search terms for lists are declared with '?' and '~term' in next subfield
    ##     E.g. {"specific_bucket": "Buckets/?/Name~CloudCopyCat"}
    ## Method args dict can contain refs to objects in state when wrapped as a Resource
    ##   Referencing value in Resource.state is declared with '$'
    ##     E.g. {"TopicArn": "$dest_sns_topic/arn"}
    def __init__(
            self,
            client=None,
            method: str=None,
            method_args: dict[str]=None,
            output_keys: dict[str]=None
        ):
        self.client = client
        self.method = method
        self.method_args = method_args
        self.expected_output = output_keys
        self.output = None
        self.exception = None

        if not method:
            print("No method provided to ApiCall")