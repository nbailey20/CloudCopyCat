from classes.ApiCall import ApiCall

class ConditionalApiCall(ApiCall):
    def execute(self, args: list[dict[str]]=[], outputs: list[dict[str]]=[]):
        execution_args = self.method_args
        if args:
            execution_args = args
        execution_outputs = self.output
        if outputs:
            execution_outputs = outputs
        api_res = super().execute(execution_args, execution_outputs)
        return api_res


    def eval_expression(self, expression_args: dict[str]={}):
        if self.expression_func == None:
            return
        if expression_args:
            self.expression_args = expression_args
        method_idx = self.expression_func(**self.expression_args)
        self.method = self.method_options[method_idx]
        self.method_args = self.method_arg_options[method_idx]
        self.expected_output = self.expected_output_options[method_idx]


    ## Expression func must return an integer indicating which index of
    ##    method_options, method_arg_options, and output_key_options to use during execution
    def __init__(
            self,
            client=None,
            method_options: list[str]=[],
            method_arg_options: list[dict[str]]=[],
            output_key_options: list[dict[str]]=[],
            expression_func=None,
            expression_args: dict[str]={}
        ):
        self.client = client
        self.method_options = method_options
        self.method_arg_options = method_arg_options
        self.expected_output_options = output_key_options
        self.expression_func = expression_func
        self.expression_args = expression_args

        self.method = None
        self.method_args = None
        self.output = None
        self.exception = None