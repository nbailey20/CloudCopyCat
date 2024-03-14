import copy
from classes.Resource import Resource
from helpers.core import create_session, get_account_id


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
        for region in self.regions:
            ## be careful not to change self.state when aggregating!
            regional_state = copy.deepcopy(self.state[region])
            for resource_name in regional_state:
                resource_state = regional_state[resource_name]
                ## handle regional Resource objects
                if type(resource_state) == dict:
                    if resource_name in agg_state:
                        agg_state[resource_name].append(resource_state)
                    else:
                        agg_state[resource_name] = [resource_state]
                
                ## handle regional ResourceGroup objects
                elif type(resource_state) == list:
                    if resource_name in agg_state:
                        agg_state[resource_name] += resource_state
                    else:
                        agg_state[resource_name] = resource_state

        ## handle global IAM objects
        for iam_resource in self.state["iam"]:
            agg_state[iam_resource] = self.state["iam"][iam_resource]
        ## handle global account ID variables
        agg_state["src_account"] = self.state["src_account"]
        agg_state["dest_account"] = self.state["dest_account"]
        return agg_state


    ## Services are given complete regional state: dict of service name => list of resource states
    ## Needed to ref values created by other services in same region
    def _set_state(self, resource: Resource, region: str):
        if resource.type == "iam":
            ## IAM is global, needs to ref resources in all regions in policy
            aggregated_state = self._aggregate_state()
            resource.set_state(aggregated_state)
        else:
            regional_state = self.state[region]
            ## add IAM resources so they can be ref'd by regional resources
            regional_state.update(self.state["iam"])
            regional_state["src_account"] = self.state["src_account"]
            regional_state["dest_account"] = self.state["dest_account"]
            regional_state["region"] = region
            resource.set_state(regional_state)


    def _update_state(self, resource: Resource, region: str):
        ## IAM services return aggregated state, extract relevant IAM state for self.state["iam"]
        if resource.type == "iam":
            for resource_name in resource.state:
                if type(resource.state[resource_name]) == list:
                    resource_list = resource.state[resource_name]
                    if not len(resource_list):
                        continue
                    ## check first resource in aggregated list to get type
                    if resource_list[0]["type"] != "iam":
                        continue
                    self.state["iam"][resource_name] = resource_list

                elif type(resource.state[resource_name]) == dict:
                    resource_dict = resource.state[resource_name]
                    if resource_dict["type"] == "iam":
                        self.state["iam"][resource_name] = resource_dict
        else:
            ## resource state is (nonaggregated) dict of all resource names in region
            regional_state = {}
            for resource_name in resource.state:
                if type(resource.state[resource_name]) == list:
                    resource_list = resource.state[resource_name]
                    if not len(resource_list):
                        continue
                    ## IAM is included in Resource.set_state(), ignore when returned
                    if resource_list[0]["type"] == "iam":
                        continue
                    regional_state[resource_name] = resource_list

                elif type(resource.state[resource_name]) == dict:
                    resource_dict = resource.state[resource_name]
                    if resource_dict["type"] != "iam":
                        regional_state[resource_name] = resource_dict
            self.state[region] = regional_state


    def _do_action(self, action: str):
        resource_list = self.resources
        if action == "delete":
                resource_list = self.resources[::-1]

        for resource in resource_list:
            for idx, region in enumerate(self.regions):
                ## only create IAM services once globally
                if idx != 0 and resource.type == "iam":
                    continue

                ## ResourceGroups can have custom numbers of resources per region
                if resource.name in self.num_resources:
                    resource.set_num_resources(self.num_resources[resource.name][region])

                client = self._get_client(resource, region)
                if not client:
                    continue
                resource.set_client(client)
                if resource.name in self.dependencies:
                    resource.set_dependencies(self.dependencies[resource.name])
                self._set_state(resource, region)

                ## perform action and update deployment state afterward
                action_func = getattr(resource, action)
                print(f"Performing {region} {resource.name} {action}")
                action_func()
                self._update_state(resource, region)


    def create(self):
        self._do_action(action="create")

    def delete(self):
        self._do_action(action="delete")


    ## clients map is resource name => client to use with resource
    ## dependencies is resource name => prerequisite resource names list
    ## num resources is resource name => region => num resources to create in region
    ##     only needed for ResourceGroups
    ## any service names starting with "src" are created with src_profile clients
    ## any service names starting with "dest" are created in dest_profile clients
    def __init__(
            self,
            src_profile: str=None,
            dest_profile: str=None,
            regions: list[str]=[],
            resources: tuple[Resource]=(),
            num_resources: dict={},
            dependencies: dict={},
            state: dict={}
        ):
        self.src_profile = src_profile
        self.dest_profile = dest_profile
        self.regions = regions
        self.resources = resources
        self.num_resources = num_resources
        self.dependencies = dependencies
        self.state = state
        self.clients_map = {}
        if not self.state:
            self.state = {
                "iam": {},
                "src_account": get_account_id(self.src_profile),
                "dest_account": get_account_id(self.dest_profile)
            }
        for region in self.regions:
            for resource in self.resources:
                empty_state = {"arn": None, "type": resource.type}
                if resource.name in self.num_resources:
                    empty_state = [empty_state] * self.num_resources[resource.name][region]
                if resource.type == "iam":
                    if resource.name in self.state["iam"]:
                        continue
                    self.state["iam"][resource.name] = empty_state
                else:
                    if resource.name in self.state[region]:
                        continue
                    self.state[region][resource.name] = empty_state