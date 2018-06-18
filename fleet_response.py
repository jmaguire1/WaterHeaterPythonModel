# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

from datetime import datetime


class FleetResponse:
    """
    This class describes 1-timestep output of a fleet
    """

    def __init__(self, ts=datetime.utcnow()):
        """
        Constructor with default values
        """
        self.ts = ts
        self.P_injected = None
        self.Q_injected = None
        self.Q_service = None
        self.P_service = None

        self.P_service_max = None
        self.Q_service_max = None
        self.P_injected_max = None
        self.E = None
        self.P_dot = None
        self.Q_dot = None

        self.Constraints = None

        self.Loss_standby = None
        self.Eff_throughput = None
