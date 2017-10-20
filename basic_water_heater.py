import math

class BasicWaterHeater(object):
    """ An instance of a simple water heater from gridlabd"""
    RHOWATER = 62.4
    GALPCF = 7.4805195
    BTUPHPKW = 1e3 * 3.4120

    def __init__(self, tank_setpoint=132,
                       thermostat_deadband=10,
                       heating_element_capacity=4.5,
                       tank_volume=50,
                       tank_ua=3.7,
                       current_temperature=128,
                       nominal_voltage=240,
                       inlet_temp=60):

        self.heat_needed = 0
        self.heating_element_capacity = heating_element_capacity
        self.tank_setpoint = tank_setpoint
        self.thermostat_deadband = thermostat_deadband
        self.tank_ua = tank_ua
        self.tank_volume = tank_volume
        self.inlet_temp = inlet_temp
        self.cp = 1
        self.cw = tank_volume/BasicWaterHeater.GALPCF * BasicWaterHeater.RHOWATER * self.cp;
        self.current_temperature = current_temperature
        self.nominal_voltage = nominal_voltage


    def execute(self, delta_t=None,
                      actual_voltage=None,
                      water_demand=None,
                      ambient_temp=None,
                      tank_setpoint=None,
                      ):

        """ Calculate next temperature and load"""
        self.tank_setpoint = tank_setpoint

        # print(self.tank_setpoint)

        mdot_Cp = self.cp * water_demand * 60 * BasicWaterHeater.RHOWATER / BasicWaterHeater.GALPCF

        c1 = (self.tank_ua + mdot_Cp) / self.cw

        actual_kW = (self.heat_needed*self.heating_element_capacity *
                     (actual_voltage*actual_voltage) /
                     (self.nominal_voltage*self.nominal_voltage))

        c2 = (actual_kW*BasicWaterHeater.BTUPHPKW +
              mdot_Cp*self.inlet_temp +
              self.tank_ua*ambient_temp)/(self.tank_ua + mdot_Cp)

        new_temp = c2 - (c2 - self.current_temperature) * math.exp(-c1 * delta_t )

        #internal_gain = self.tank_ua * (new_temp - ambient_temp);

        Tlower  = self.tank_setpoint - self.thermostat_deadband/2.0;
        Tupper = self.tank_setpoint + self.thermostat_deadband/2.0;

        if( new_temp <= Tlower + 0.02):
            self.heat_needed = 1
        elif( new_temp >= Tupper - 0.02):
            self.heat_needed = 0

        self.current_temperature = new_temp
        return {'temperature': new_temp,
                'load': actual_kW}
