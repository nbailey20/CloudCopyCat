from classes.Resource import Resource
from helpers.core import create_session


class Deployment():
    def _get_client(self, resource: Resource, client_region: str):
        profile = self.dest_profile
        if resource.name.startswith("src"):
            profile = self.src_profile
        if not profile:
            return None
        
        session = create_session(profile, region=client_region)
        client_key = f"{session.profile_name}{client_region}{resource.type}"
        if client_key in self.clients_map:
            return self.clients_map[client_key]
        else:
            client = session.client(resource.type)
            self.clients_map[client_key] = client
            return client
        

    def _set_state(self, resource, region):
        if resource.type == "iam": ## IAM is global
            resource.set_state(self.state)
        else:
            resource.set_state(self.state[region])

    def _update_state(self, resource, region):
        if resource.type == "iam":
            self.state = resource.state
        else:
            self.state[region] = resource.state


    def _do_action(self, action: str):
        num_resources = len(self.resources)
        for region in self.regions:
            for idx, resource in enumerate(self.resources):
                ## only create IAM resources once globally
                if idx != num_resources-1 and resource.type == "iam":
                    continue

                client = self._get_client(resource, region)
                if not client:
                    continue
                resource.set_client(client)
                self._set_state(resource, region)

                ## perform action and update deployment state afterward
                action_func = getattr(resource, action)
                action_func()
                self._update_state(resource, region)


    def create(self):
        self._do_action(action="create")

    def delete(self):
        self._do_action(action="delete")


    ## clients map is resource name => client to use with resource
    def __init__(
            self,
            src_profile: str=None,
            dest_profile: str=None,
            regions: list[str]=[],
            resources: tuple[Resource]=()
        ):
        self.src_profile = src_profile
        self.dest_profile = dest_profile
        self.regions = regions
        self.resources = resources
        self.clients_map = {}
        self.state = {}
        for region in self.regions:
            self.state[region] = {}
            for resource in self.resources:
                self.state[region][resource.name] = {
                    "arn": None,
                    "configs": {}
                }