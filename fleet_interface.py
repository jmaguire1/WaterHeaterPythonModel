# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}


class FleetInterface:
    """
    This class is base class for all services
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        pass

    def process_request(self, ts, P_req, Q_req):
        """
        Request for timestep ts

        :param P_req:
        :param Q_req:

        :return res: an instance of FleetResponse
        """
        pass

    def forecast(self, requests):
        """
        Request for current timestep

        :param requests: list of  requests

        :return res: list of FleetResponse
        """
        pass

    def change_config(self, **kwargs):
        """
        This function is here for future use. The idea of having it is for a service to communicate with a fleet
        in a nondeterministic manner during a simulation

        :param kwargs: a dictionary of (key, value) pairs. The exact keys are decided by a fleet.

        Example: Some fleets can operate in an autonomous mode, where they're not responding to requests,
        but watching, say, the voltage. If the voltage dips below some defined threshold (which a service might define),
        then the fleet responds in a pre-defined way.
        In this example, the kwargs can be {"voltage_threshold": new_value}
        """
        pass
