from botocore.exceptions import ClientError

class ApiCall():
    ## Recurse through API response JSON
    ## to collect value(s) at output path
    def _get_output(self, api_res, output_path):
        if not output_path:
            return None
        if len(output_path) == 1:
            return api_res[output_path[0]]
        if output_path[0] == "*":
            return [self._get_output(api_sub_res, output_path[1:]) 
                    for api_sub_res in api_res]
        else:
            return self._get_output(api_res[output_path[0]], output_path[1:])


    ## Set self.output to be dict containing output_key => output_values
    def _set_outputs(self, api_res, output_keys):
        if not output_keys:
            return

        self.output = {}
        for key in output_keys:
            output_path = output_keys[key].split("/")
            self.output[key] = self._get_output(api_res, output_path)


    ## Make API call to method with method_args
    ## Outputs dict determines which values from API response are returned
    ##  {name of output => path in API response where value is found}
    ##   Nested JSON values are declared with '/'
    ##   E.g. {"bucket_owner": "Owner/DisplayName"}
    ##   All values in list are declared with '*'
    ##   E.g. {"all_buckets": "Buckets/*/Name"}
    def __init__(self, client, method=None, method_args=None, output_keys=None):
        self.output = None

        if not method:
            print("No method provided, skipping")
            return
        try:
            method_to_call = getattr(client, method)
        except:
            print(f"Action {method} not known for client, skipping")
            return

        try:
            api_res = None
            if method_args:
                api_res = method_to_call(**method_args)
            else:
                api_res = method_to_call()

        except ClientError as e:
            if e.response['Error'] and e.response['Error']['Code'] in ['AccessDenied', 'AccessDeniedException']:
                print(f'CloudCopyCat does not have permission to perform {method}, skipping')
            elif e.response['Error'] and e.response['Error']['Code'] in ['NotFoundException', 'NoSuchEntity']:
                print(f'Resource not found exception received from AWS client: {e}')
            else:
                print(f'AWS client error: {e}')
            return

        except Exception as e:
            print(f'Unknown API error, exiting: {e}')
            return

        self._set_outputs(api_res, output_keys)