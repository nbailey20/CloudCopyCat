from classes.Resource import Resource
from classes.ResourceGroup import ResourceGroup
from helpers.core import create_session


class Deployment():
    def _get_client(self, service: Service, client_region: str):
        profile = self.dest_profile
        if service.name.startswith("src"):
            profile = self.src_profile
        if not profile:
            return None

        session = create_session(profile, region=client_region)
        client_key = f"{session.profile_name}{client_region}{service.type}"
        if client_key in self.clients_map:
            return self.clients_map[client_key]
        else:
            client = session.client(service.type)
            self.clients_map[client_key] = client
            return client
        

    def _aggregate_state(self):
        agg_state = {}
        ## yes this is not optimal but don't know a cleaner way
        for region in [k for k in self.state.keys() if k != "iam"]:
            regional_state = self.state[region]
            for service_name in regional_state:
                agg_state[service_name] = []
                regional_resources = regional_state[service_name]



                for resource in [r for r in regional_services if r["type"] != "type"]:
                    if not service_name in agg_state:
                        agg_state[service_name] = {"type": regional_service["type"]}
                    if not key in agg_state[service_name]:
                        agg_state[service_name][key] = [regional_service[key]]
                    else:
                        agg_state[service_name][key].append(regional_service[key])

        for key in self.state["iam"]:
            agg_state[key] = self.state["iam"][key]
        return agg_state


    ## Services are given complete regional state: dict of service name => list of resource states
    ## Needed to ref values created by other services in same region
    def _set_state(self, service: Service, region: str):
        if service.type == "iam":
            ## IAM is global, needs to ref services in all regions in policy
            aggregated_state = self._aggregate_state()
            service.set_state(aggregated_state)
        else:
            regional_state = self.state[region]
            ## add IAM resources so they can be ref'd by regional resources
            regional_state.update(self.state["iam"])
            service.set_state(self.state[region])


    def _update_state(self, service, region):
        ## IAM services return aggregated state, add relevant IAM state to self.state
        if service.type == "iam":
            for service_name in service.state:
                resource_list = service.state[service_name]
                ## check first resource in service to get type
                if not len(resource_list):
                    continue
                if resource_list[0]["type"] != "iam":
                    continue
                self.state["iam"][service_name] = service.state[service_name]
        else:
            ## service state is dict of all services in region
            ## IAM is included in set_state(), ignore when returned
            regional_state = {}
            for service_name in service.state:
                resource_list = service.state[service_name]
                if not len(resource_list):
                    continue
                if resource_list[0]["type"] == "iam":
                    continue
                regional_state[service_name] = service.state[service_name]
            self.state[region] = regional_state


    def _do_action(self, action: str):
        num_regions = len(self.regions)
        for idx, region in enumerate(self.regions):
            ## delete resources in opposite order they were created
            service_list = self.services
            if action == "delete":
                service_list = self.services[::-1]

            for service in service_list:
                ## only create IAM services once globally
                if idx != num_regions-1 and service.type == "iam":
                    continue

                client = self._get_client(service, region)
                if not client:
                    continue
                service.set_client(client)
                if service.name in self.dependencies:
                    service.set_dependencies(self.dependencies[service.name])
                self._set_state(service, region)

                ## perform action and update deployment state afterward
                action_func = getattr(service, action)
                action_func()
                self._update_state(service, region)


    def create(self):
        self._do_action(action="create")

    def delete(self):
        self._do_action(action="delete")


    ## clients map is resource name => client to use with resource
    ## dependencies is resource name => prerequisite resource names list
    ## any service names starting with "src" are created with src_profile clients
    ## any servic names starting with "dest" are created in dest_profile clients
    def __init__(
            self,
            src_profile: str=None,
            dest_profile: str=None,
            regions: list[str]=[],
            services: tuple[Service]=(),
            dependencies: dict[list[str]]={}
        ):
        self.src_profile = src_profile
        self.dest_profile = dest_profile
        self.regions = regions
        self.services = services
        self.dependencies = dependencies
        self.clients_map = {}
        self.state = {"iam": {}}
        for region in self.regions:
            self.state[region] = {}
            for service in self.services:
                if service.type == "iam":
                    self.state["iam"][service.name] = {"arn": None, "type": "iam"}
                else:
                    self.state[region][service.name] = {"arn": None, "type": service.type}