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
        

    def _aggregate_state(self):
        agg_state = {}
        ## yes this is not optimal but don't know a cleaner way
        for region in [k for k in self.state.keys() if k != "iam"]:
            regional_state = self.state[region]
            for resource_name in regional_state:
                regional_resource = regional_state[resource_name]
                for key in [k for k in regional_resource if k != "type"]:
                    if not resource_name in agg_state:
                        agg_state[resource_name] = {"type": regional_resource["type"]}
                    if not key in agg_state[resource_name]:
                        agg_state[resource_name][key] = [regional_resource[key]]
                    else:
                        agg_state[resource_name][key].append(regional_resource[key])

        for key in self.state["iam"]:
            agg_state[key] = self.state["iam"][key]
        return agg_state


    def _set_state(self, resource, region):
        if resource.type == "iam":
            ## IAM is global, needs to ref resources in all regions in policy
            aggregated_state = self._aggregate_state()
            resource.set_state(aggregated_state)
        else:
            resource.set_state(self.state[region])


    def _update_state(self, resource, region):
        ## IAM returns aggregated state, add relevant IAM state to self.state
        if resource.type == "iam":
            for key in resource.state:
                resource_obj = resource.state[key]
                if resource_obj["type"] != "iam":
                    continue
                self.state["iam"][key] = resource.state[key]
        else:
            self.state[region] = resource.state


    def _do_action(self, action: str):
        num_regions = len(self.regions)
        for idx, region in enumerate(self.regions):
            ## delete resources in opposite order they were created
            resource_list = self.resources
            if action == "delete":
                resource_list = self.resources[::-1]

            for resource in resource_list:
                ## only create IAM resources once globally
                if idx != num_regions-1 and resource.type == "iam":
                    continue

                client = self._get_client(resource, region)
                if not client:
                    continue
                resource.set_client(client)
                if resource.name in self.dependencies:
                    resource.set_dependencies(self.dependencies[resource.name])
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
    ## dependencies is resource name => prerequisite resource names list
    def __init__(
            self,
            src_profile: str=None,
            dest_profile: str=None,
            regions: list[str]=[],
            resources: tuple[Resource]=(),
            dependencies: dict[list[str]]={}
        ):
        self.src_profile = src_profile
        self.dest_profile = dest_profile
        self.regions = regions
        self.resources = resources
        self.dependencies = dependencies
        self.clients_map = {}
        self.state = {"iam": {}}
        for region in self.regions:
            self.state[region] = {}
            for resource in self.resources:
                if resource.type == "iam":
                    self.state["iam"][resource.name] = {"arn": None, "type": "iam"}
                else:
                    self.state[region][resource.name] = {"arn": None, "type": resource.type}