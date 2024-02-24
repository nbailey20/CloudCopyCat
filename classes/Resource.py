from classes.ApiCall import ApiCall
from helpers.core import get_dict_value_from_expression

class Resource():
    def _update_state(self, api_output: dict[str]):
        if not api_output:
          #  print("No output returned from API")
            return
        for key in api_output:
            if key == "arn":
                self.state[self.name]["arn"] = api_output[key]
            else:
                self.state[self.name]["configs"][key] = api_output[key]


    def _render_method_args(self, args: dict[str]):
        if not args:
            return
        rendered_args = {}
        for key in args:
            rendered_args[key] = args[key]
            if args[key][0] == "$":
                expression = args[key][1:].split("/")
                rendered_args[key] = get_dict_value_from_expression(self.state, expression)
        return rendered_args


    def _invoke_apis(self, api_type: str):
        apis = self.create_apis
        if api_type == "describe":
            apis = self.describe_apis
        elif api_type == "delete":
            apis = self.delete_apis

        for a in apis:
            rendered_args = self._render_method_args(a.method_args)
            a.set_client(self.client)
            a.execute(args=rendered_args)
            if a.exception:
                print(f"Received exception while executing ApiCall: {a.exception}")
                if api_type == "create":
                    print("Cleaning up Resource")
                    self.delete()
                break
            self._update_state(a.output)


    def set_client(self, client):
        self.client = client

    def set_state(self, state):
        self.state = state

    def create(self):
        self._invoke_apis(api_type="describe")
        if not self.state[self.name]["arn"]:
            self._invoke_apis(api_type="create")

    def describe(self):
        self._invoke_apis(api_type="describe")

    def delete(self):
        self._invoke_apis(api_type="delete")
        ## delete doesn't update state, call describe after deletion
        self._invoke_apis(api_type="describe")


    def __init__(
            self,
            name: str,
            type: str,
            client=None,
            create_apis: tuple[ApiCall]=(),
            describe_apis: tuple[ApiCall]=(),
            delete_apis: tuple[ApiCall]=(),
            state: dict={}
        ):
        self.name = name
        self.type = type
        self.client = client
        self.create_apis = create_apis
        self.describe_apis = describe_apis
        self.delete_apis = delete_apis
        self.state = state
        if not self.state:
            self.state = {
                self.name: {
                    "arn": None,
                    "configs": {}
                }
            }
