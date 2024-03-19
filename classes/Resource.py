import re
import json
from classes.ApiCall import ApiCall
from helpers.log import logger
from helpers.core import get_value_from_expression

class Resource():
    def _update_state(self, api_output: dict[str]):
        if not api_output:
            return
        self.state[self.name].update(api_output)


    def _render_method_arg(self, arg: str):
        if type(arg) != str:
            return arg

        ## Render other API method args, indicated with "@"
        if arg.startswith("@"):
            other_method = arg[1:]
            all_apis = self.create_apis + self.describe_apis + self.delete_apis
            for api in all_apis:
                if api.method == other_method:
                    return api.method_args
        
        ## Render values stored in state, indicated with "$" or "${}"
        updated_arg = arg
        renderable_str = re.search(r"(\"*)\$\{*([\w/#]+)\}*(\"*)", arg)
        while renderable_str:
            start_idx, end_idx = renderable_str.span()

            ## render any #id terms into list indexes, e.g. #4
            partial_str = re.sub(r"#id", f"#{self.id}", renderable_str.group(2))
            rendered_str = get_value_from_expression(
                self.state,
                partial_str,
            )
            if type(rendered_str) != str:
                rendered_str = json.dumps(rendered_str)
            ## only keep surrounding quotes when rendered value is a string
            elif type(rendered_str) == str:
                rendered_str = renderable_str.group(1) + rendered_str + renderable_str.group(3)
            updated_arg = updated_arg[:start_idx] + rendered_str + updated_arg[end_idx:]
            renderable_str = re.search(r"(\"*)\$\{*([\w/#]+)\}*(\"*)", updated_arg)
        return updated_arg


    ## Method args can contain refs to outputs stored in state when wrapped 
    ##   as a Deployment containing Resource/ResourceGroups
    ##   Referencing value in Resource.state is declared with '$' and '#id' for specific index in ResourceGroup
    ##     E.g. {"TopicArn": "$dest_sns/#id/arn"}
    ##   If a property for all resources is desired, use '#all'
    ## Method args can contain refs to other method args when wrapped
    ##   as a Deployment containing Resource/ResourceGroups
    ##   Referencing method args is declared with '@' and method name for corresponding ApiCall
    ##     E.g. {"other_args": "@create_bucket"}
    def _render_method_args(self, args: dict[str]):
        if not args:
            return args
        ## recurse over iterables
        if type(args) == list:
            return [self._render_method_args(element) for element in args]
        if type(args) == dict:
            return {key: self._render_method_args(value) for (key,value) in args.items()}
        ## render individual str/bytes
        if type(args) == str:
            return self._render_method_arg(args)
        if type(args) == bytes:
            return bytes(self._render_method_arg(args.decode()), encoding="utf-8")
        ## don't attempt to render any other types
        return args


    def _invoke_apis(self, api_type: str):
        apis = self.create_apis
        if api_type == "describe":
            apis = self.describe_apis
        elif api_type == "delete":
            apis = self.delete_apis

        for api in apis:
            api.exception = None

            ## Evaluate any conditional APIs
            if hasattr(api, "expression_func"):
                api.eval_expression(self._render_method_args(api.expression_args))

            rendered_args = self._render_method_args(api.method_args)
            rendered_outputs = self._render_method_args(api.expected_output)
            api.set_client(self.client)
            api.execute(args=rendered_args, outputs=rendered_outputs)
            if api.exception:
                logger.debug(f"Received exception while executing ApiCall: {api.exception}")
                if api_type == "create":
                    logger.info("Could not fully create Resource, cleaning up before retry")
                    self.delete()
                    break
            self._update_state(api.output)


    def set_id(self, id):
        self.id = id

    def set_client(self, client):
        self.client = client

    def set_state(self, state):
        self.state = state

    def set_dependencies(self, deps):
        self.dependencies = deps

    def _check_dependencies(self):
        for dep in self.dependencies:
            if dep not in self.state:
                return False

            dep_test = None
            if type(self.state[dep]) == dict:
                dep_test = self.state[dep]["arn"]
            elif type(self.state[dep]) == list:
                dep_test = all([r["arn"] for r in self.state[dep]])
            else:
                logger.debug(f"Unexpected type for self.dependencies: {type(self.state[dep])}")
            if not dep_test:
                logger.info(f"Prerequisite resource {dep} not found")
                return False
        return True

    def _check_if_exists(self):
        if self.state[self.name]["arn"]:
            return True
        return False

    def create(self):
        if not self._check_dependencies():
            logger.info(f"Not all dependencies met for {self.name}, skipping creation")
            return
        self._invoke_apis(api_type="describe")
        if not self._check_if_exists():
            logger.info(f"Creating {self.name}, no existing resource found")
            self._invoke_apis(api_type="create")
        else:
            logger.info(f"Resource {self.name} already exists, skipping creation")

    def describe(self):
        self._invoke_apis(api_type="describe")

    def delete(self):
        self._invoke_apis(api_type="describe")
        if self._check_if_exists():
            self._invoke_apis(api_type="delete")
            ## delete doesn't update state, call describe after deletion
            self._invoke_apis(api_type="describe")
            if not self._check_if_exists():
                logger.info(f"Successfully deleted Resource {self.name}")
        else:
            logger.info(f"Resource {self.name} does not exist, nothing to clean up")


    def __init__(
            self,
            name: str,
            type: str,
            client=None,
            create_apis: tuple[ApiCall]=(),
            describe_apis: tuple[ApiCall]=(),
            delete_apis: tuple[ApiCall]=(),
            dependencies: list[str]=[],
            state: dict={}
        ):
        self.name = name
        self.type = type
        self.client = client
        self.create_apis = create_apis
        self.describe_apis = describe_apis
        self.delete_apis = delete_apis
        self.dependencies = dependencies
        self.state = state
        if not self.state:
            self.state = {
                self.name: {"arn": None, "type": self.type}
            }

        self.id = 0 ## used if Resource is included in a ResourceGroup
