
## Implements same methods as ApiCall
## Can be passed as a Resource API when data transformation is required
##   between one API's output and the next API's method_args
class Transformer():
    def execute(self, args: dict[str]=None):
        func_args = self.method_args
        if args:
            func_args = args

        func_res = None
        if not func_args:
           func_res = self.method()
        else:
            func_res = self.method(**func_args)
        self._store_outputs(func_res)


    ## Set self.output to be dict containing output_key => output_values
    def _store_outputs(self, func_res: dict[str]):
        if not self.expected_output:
            return
        self.output = {}
        for key in self.expected_output:
            if not key in func_res:
                self.output[key] = None
            else:
                self.output[key] = func_res[key]


    def set_client(self, _):
        pass


    def __init__(
            self,
            func=None,
            function_args: dict[str]=None,
            output_keys: list[str]=None
        ):
        self.method = func
        self.method_args = function_args
        self.expected_output = output_keys
        self.output = None
        self.exception = None
