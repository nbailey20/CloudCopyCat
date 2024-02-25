import re

from classes.ApiCall import ApiCall
from helpers.core import get_value_from_expression

class Resource():
    def _update_state(self, api_output: dict[str]):
        if not api_output:
          #  print("No output returned from API")
            return
        for key in api_output:
            self.state[self.name][key] = api_output[key]

    ## ApiClass can contain refs to objects in state when wrapped as a Resource
    ##   Referencing value in Resource.state is declared with '$'
    ##     E.g. {"TopicArn": "$dest_sns_topic/arn"}
    def _render_method_args(self, args: dict[str]):
        if not args:
            return
        rendered_args = {}
        for key in args:
            rendered_args[key] = args[key]
            if type(args[key]) == str:
                val_to_render = re.search(r"(\$[\w/]+)", rendered_args[key])
                while val_to_render:
                    rendered_val = get_value_from_expression(
                        self.state,
                        val_to_render.group(1)[1:], ## remove leading $
                        value_type="arg"
                    )
                    temp = re.sub(
                        "\\"+val_to_render.group(1), ## need to escape $ so it can be subbed
                        str(rendered_val),
                        rendered_args[key]
                    )
                    rendered_args[key] = temp
                    val_to_render = re.search(r"(\$[\w/]+)", rendered_args[key])
            ## if method args contain nested dict, recurse over those keys
            elif type(args[key]) == dict:
                rendered_args[key] = self._render_method_args(args[key])
        return rendered_args



    def _invoke_apis(self, api_type: str):
        apis = self.create_apis
        if api_type == "describe":
            apis = self.describe_apis
        elif api_type == "delete":
            apis = self.delete_apis

        for api in apis:
            rendered_args = self._render_method_args(api.method_args)
            api.set_client(self.client)
            api.execute(args=rendered_args)
            if api.exception:
                print(f"Received exception while executing ApiCall: {api.exception}")
                if api_type == "create":
                    print("Cleaning up Resource")
                    self.delete()
                break
            self._update_state(api.output)


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
                print(f"Unexpected type for self.dependencies: {type(self.state[dep])}")
            if not dep_test:
                print(f"Prerequisite resource {dep} not found")
                return False
        return True

    def create(self):
        if not self._check_dependencies():
            print(f"Not all dependencies met for {self.name}, skipping creation")
            return
        self._invoke_apis(api_type="describe")
        if not self.state[self.name]["arn"]:
            print(f"No existing resource found, creating {self.name}")
            self._invoke_apis(api_type="create")

    def describe(self):
        self._invoke_apis(api_type="describe")

    def delete(self):
        if self.state[self.name]["arn"]:
            self._invoke_apis(api_type="delete")
            ## delete doesn't update state, call describe after deletion
            self._invoke_apis(api_type="describe")
        else:
            print("Resource ARN is null, nothing to clean up")


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
