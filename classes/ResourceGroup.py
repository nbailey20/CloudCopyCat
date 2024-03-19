from classes.ApiCall import ApiCall
from classes.Resource import Resource
from helpers.log import logger


## Stores multiple Resource states as list under a single Resource name
class ResourceGroup(Resource):
    def _update_state(self, api_output: dict[str]):
        if not api_output:
            return
        ## include resource type in state
        api_output.update({"type": self.type})
        if not len(self.state[self.name]):
            self.state[self.name] = [api_output]
        elif len(self.state[self.name]) > self.id:
            self.state[self.name][self.id].update(api_output)
        else:
            logger.debug("ResourceGroup state contains unexpected number of items in list")

    def _check_if_exists(self):
        ## if we don't have enough resources yet, must not exist
        if len(self.state[self.name])-1 < self.id:
            return False
        if self.state[self.name][self.id]["arn"]:
            return True
        return False

    def create(self):
        for idx in range(self.num_resources):
            self.id = idx
            super().create()

    def describe(self):
        for idx in range(self.num_resources):
            self.id = idx
            super().describe()

    def delete(self):
        for idx in range(self.num_resources):
            self.id = idx
            super().delete()


    def set_num_resources(self, num_resources):
        self.num_resources = num_resources


    def __init__(
            self,
            name: str,
            type: str,
            client=None,
            num_resources: int=None,
            create_apis: tuple[ApiCall]=(),
            describe_apis: tuple[ApiCall]=(),
            delete_apis: tuple[ApiCall]=(),
            dependencies: dict[list[str]]={},
            state: dict={}
        ):

        self.name = name
        self.state = state
        if not self.state:
            self.state = {
                self.name: []
            }
        super().__init__(
            name,
            type,
            client,
            create_apis,
            describe_apis,
            delete_apis,
            dependencies,
            self.state
        )
        self.num_resources = num_resources