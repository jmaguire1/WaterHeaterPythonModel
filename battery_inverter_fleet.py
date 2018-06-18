# -*- coding: utf-8 -*- {{{
#
# Your license here
# }}}

import configparser
from fleet_interface import FleetInterface
#from fleet_request import FleetRequest
from fleet_response import FleetResponse
import numpy   

class BatteryInverterFleet(FleetInterface):
    """
    This class implements FleetInterface so that it can communicate with a fleet
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor
        """
        

        # Read config file
        self.config = configparser.ConfigParser()
        self.config.read('config_CRM.ini')

        # Load config info with default values if there is no such config param in the config file
        self.name = self.config.get('Config Values', 'Name', fallback='Fallback/default Battery Name')
        self.model_type = self.config.get('Config Values', 'ModelType', fallback='Not Defined')
        
        # Load different parameters for the energy reservoir model (self), or the charge reservoir model (self)
        if self.model_type == "ERM":
            self.max_power_charge = float(self.config.get('Config Values', 'MaxPowerCharge', fallback=10))
            self.max_power_discharge = float(self.config.get('Config Values', 'MaxPowerDischarge', fallback=10))
            self.max_apparent_power = float(self.config.get('Config Values', 'MaxApparentPower', fallback=-10))
            self.min_pf = float(self.config.get('Config Values', 'MinPF', fallback=0.8))
            self.max_soc = float(self.config.get('Config Values', 'MaxSoC', fallback=100))
            self.min_soc = float(self.config.get('Config Values', 'MinSoC', fallback=0))
            self.energy_capacity = float(self.config.get('Config Values', 'EnergyCapacity', fallback=10))
            self.energy_efficiency = float(self.config.get('Config Values', 'EnergyEfficiency', fallback=1))
            self.self_discharge_power = float(self.config.get('Config Values', 'SelfDischargePower', fallback=0))
            self.max_ramp_up = float(self.config.get('Config Values', 'MaxRampUp', fallback=10))
            self.max_ramp_down = float(self.config.get('Config Values', 'MaxRampDown', fallback=10))
            self.num_of_devices = float(self.config.get('Config Values', 'NumberOfDevices', fallback=10))
            # self states
            self.t = float(self.config.get('Config Values', 't', fallback=10))
            self.soc = float(self.config.get('Config Values', 'soc', fallback=10))
            self.cap = float(self.config.get('Config Values', 'cap', fallback=10))
            self.maxp = float(self.config.get('Config Values', 'maxp', fallback=10))
            self.minp = float(self.config.get('Config Values', 'minp', fallback=10))
            self.maxp_fs = float(self.config.get('Config Values', 'maxp_fs', fallback=10))
            self.rru = float(self.config.get('Config Values', 'rru', fallback=10))
            self.rrd = float(self.config.get('Config Values', 'rrd', fallback=10))
            self.ceff = float(self.config.get('Config Values', 'ceff', fallback=10))
            self.deff = float(self.config.get('Config Values', 'deff', fallback=10))
            self.P_req =float( self.config.get('Config Values', 'P_req', fallback=10))
            self.Q_req = float(self.config.get('Config Values', 'Q_req', fallback=10))
            self.P_injected = float(self.config.get('Config Values', 'P_injected', fallback=0))
            self.Q_injected = float(self.config.get('Config Values', 'Q_injected', fallback=0))
            self.P_service = float(self.config.get('Config Values', 'P_service', fallback=0))
            self.Q_service = float(self.config.get('Config Values', 'Q_service', fallback=0))
            self.es = float(self.config.get('Config Values', 'es', fallback=10))

        elif self.model_type == "CRM":
            # inverter parameters
            self.inv_name = self.config.get('Config Values', 'InvName', fallback='Name')
            self.inv_type = self.config.get('Config Values', 'InvType', fallback='Not Defined')
            self.coeff_0 = float(self.config.get('Config Values', 'Coeff0', fallback=0))
            self.coeff_1 = float(self.config.get('Config Values', 'Coeff1', fallback=1))
            self.coeff_2 = float(self.config.get('Config Values', 'Coeff2', fallback=0))
            self.max_power_charge = float(self.config.get('Config Values', 'MaxPowerCharge', fallback=10))
            self.max_power_discharge = float(self.config.get('Config Values', 'MaxPowerDischarge', fallback=-10))
            self.max_apparent_power = float(self.config.get('Config Values', 'MaxApparentPower', fallback=-10))
            self.min_pf = float(self.config.get('Config Values', 'MinPF', fallback=0.8))
            self.max_ramp_up = float(self.config.get('Config Values', 'MaxRampUp', fallback=10))
            self.max_ramp_down = float(self.config.get('Config Values', 'MaxRampDown', fallback=10))
            # battery parameters
            self.bat_name = self.config.get('Config Values', 'BatName', fallback='Name')
            self.bat_type = self.config.get('Config Values', 'BatType', fallback='Not Defined')
            self.n_cells = float(self.config.get('Config Values', 'NCells', fallback=10))
            self.voc_model_type = self.config.get('Config Values', 'VOCModelType', fallback='Linear')
            if self.voc_model_type == 'Linear': # note all model values assume SoC ranges from 0% to 100%
                self.voc_model_m = float(self.config.get('Config Values', 'VOC_Model_M', fallback=0.005))
                self.voc_model_b = float(self.config.get('Config Values', 'VOC_Model_b', fallback=1.8))
            if self.voc_model_type == 'Quadratic':
                self.voc_model_a = float(self.config.get('Config Values', 'VOC_Model_A', fallback=0.005))
                self.voc_model_b = float(self.config.get('Config Values', 'VOC_Model_B', fallback=1.8))
                self.voc_model_c = float(self.config.get('Config Values', 'VOC_Model_C', fallback=1.8))
            if self.voc_model_type == 'Cubic':
                self.voc_model_a = float(self.config.get('Config Values', 'VOC_Model_A', fallback=0.005))
                self.voc_model_b = float(self.config.get('Config Values', 'VOC_Model_B', fallback=1.8))
                self.voc_model_c = float(self.config.get('Config Values', 'VOC_Model_C', fallback=1.8))
                self.voc_model_d = float(self.config.get('Config Values', 'VOC_Model_D', fallback=1.8))
            if self.voc_model_type == 'CubicSpline':
                SoC_list = self.config.get('Config Values', 'VOC_Model_SOC_LIST', fallback=0.005)
                list_hold = SoC_list.split(',')
                self.voc_model_SoC_list = [float(e) for e in list_hold]
                a_list = self.config.get('Config Values', 'VOC_Model_A', fallback=0.005)
                b_list = self.config.get('Config Values', 'VOC_Model_B', fallback=0.005)
                c_list = self.config.get('Config Values', 'VOC_Model_C', fallback=0.005)
                d_list = self.config.get('Config Values', 'VOC_Model_D', fallback=0.005)
                list_hold = a_list.split(',')
                self.voc_model_a = [float(e) for e in list_hold]
                list_hold = b_list.split(',')
                self.voc_model_b = [float(e) for e in list_hold]
                list_hold = c_list.split(',')
                self.voc_model_c = [float(e) for e in list_hold]
                list_hold = d_list.split(',')
                self.voc_model_d = [float(e) for e in list_hold]
            self.max_current_charge = float(self.config.get('Config Values', 'MaxCurrentCharge', fallback=10))
            self.max_current_discharge = float(self.config.get('Config Values', 'MaxCurrentDischarge', fallback=-10))
            self.max_voltage = float(self.config.get('Config Values', 'MaxVoltage', fallback=58))
            self.min_voltage= float(self.config.get('Config Values', 'MinVoltage', fallback=48))
            self.max_soc = float(self.config.get('Config Values', 'MaxSoC', fallback=100))
            self.min_soc = float(self.config.get('Config Values', 'MinSoC', fallback=0))
            self.charge_capacity = float(self.config.get('Config Values', 'ChargeCapacity', fallback=10))
            self.coulombic_efficiency = float(self.config.get('Config Values', 'CoulombicEfficiency', fallback=1))
            self.self_discharge_current = float(self.config.get('Config Values', 'SelfDischargeCurrent', fallback=0))
            self.r0 = float(self.config.get('Config Values', 'R0', fallback=0))
            self.r1 = float(self.config.get('Config Values', 'R1', fallback=0))
            self.r2 = float(self.config.get('Config Values', 'R2', fallback=0))
            self.c1 = float(self.config.get('Config Values', 'C1', fallback=0))
            self.c2 = float(self.config.get('Config Values', 'C2', fallback=0))
            # fleet parameters
            self.num_of_devices = int(self.config.get('Config Values', 'NumberOfDevices', fallback=10))
            # self states
            self.t = float(self.config.get('Config Values', 't', fallback=0))
            self.soc = float(self.config.get('Config Values', 'soc', fallback=50))
            self.v1 = float(self.config.get('Config Values', 'v1', fallback=0))
            self.v2 = float(self.config.get('Config Values', 'v2', fallback=0))
            self.voc = float(self.config.get('Config Values', 'voc', fallback=53))
            self.vbat = float(self.config.get('Config Values', 'vbat', fallback=53))
            self.ibat = float(self.config.get('Config Values', 'ibat', fallback=0))
            self.pdc = float(self.config.get('Config Values', 'pdc', fallback=0))
            self.cap = float(self.config.get('Config Values', 'cap', fallback=10.6))
            self.maxp = float(self.config.get('Config Values', 'maxp', fallback=10))
            self.minp = float(self.config.get('Config Values', 'minp', fallback=-10))
            self.maxp_fs = float(self.config.get('Config Values', 'maxp_fs', fallback=0))
            self.rru = float(self.config.get('Config Values', 'rru', fallback=10))
            self.rrd = float(self.config.get('Config Values', 'rrd', fallback=-10))
            self.ceff = float(self.config.get('Config Values', 'ceff', fallback=1))
            self.deff = float(self.config.get('Config Values', 'deff', fallback=1))
            self.P_req = float(self.config.get('Config Values', 'P_req', fallback=0))
            self.Q_req = float(self.config.get('Config Values', 'Q_req', fallback=0))
            self.P_injected = float(self.config.get('Config Values', 'P_injected', fallback=0))
            self.Q_injected = float(self.config.get('Config Values', 'Q_injected', fallback=0))
            self.P_service = float(self.config.get('Config Values', 'P_service', fallback=0))
            self.Q_service = float(self.config.get('Config Values', 'Q_service', fallback=0))
            self.es = float(self.config.get('Config Values', 'es', fallback=5.3))
        else: 
            print('Error: ModelType not selected as either energy reservoir model (self), or charge reservoir model (self)')
            print('Battery-Inverter model config unable to continue. In config.ini, set ModelType to self or self')

    def process_request(self, ts, P_req, Q_req):
        """
        The expectation that configuration will have at least the following
        items

        :param fleet_request: an instance of FleetRequest

        :return res: an instance of FleetResponse
        """

        # call run function with proper inputs
        FleetResponse = self.run(P_req,Q_req, self.soc, ts)

        return FleetResponse

    def run(self, P_req=[0], Q_req=[0], initSoC=50, dt=1):
        P_req = P_req/self.num_of_devices
        Q_req = Q_req/self.num_of_devices

        # error checking
        if initSoC < self.min_soc or initSoC > self.max_soc:
            print('ERROR: initSoC out of range')
            return [[], []]
        elif P_req == []:
            print('ERROR: P_req vector must not be empty')
            return [[], []]
        else:
            self.t = self.t + dt
            response = FleetResponse()
            # pre-define output vectors SoC
            SoC = numpy.zeros(2)
            SoC[0] = initSoC  # initialize SoC
            p_ach = 0
            q_ach = 0

            #  Max ramp rate and aparent powerlimit checking
            if (P_req-self.P_injected) > self.max_ramp_up:
                p_ach = self.max_ramp_up
            elif (P_req-self.P_injected) < self.max_ramp_down:
                p_ach = self.max_ramp_down
            else:
                p_ach = P_req

            if (Q_req-self.Q_injected) > self.max_ramp_up:
                q_ach = self.max_ramp_up
            elif (Q_req-self.Q_injected) < self.max_ramp_down:
                q_ach = self.max_ramp_down
            else:
                q_ach = Q_req

            if p_ach < self.max_power_discharge:
                p_ach  = self.max_power_discharge
            if p_ach > self.max_power_charge:
                p_ach = self.max_power_charge
            S_req = float(numpy.sqrt(p_ach**2 + q_ach**2))
            if S_req > self.max_apparent_power:
                q_ach = float(numpy.sqrt(numpy.abs(self.max_apparent_power**2 - p_ach**2)) * numpy.sign(q_ach))
                S_req = float(numpy.sqrt(p_ach**2 + q_ach**2))
            if p_ach != 0.0:
                if float(numpy.abs(S_req/p_ach)) < self.min_pf:
                    q_ach =  float(numpy.sqrt(numpy.abs((p_ach/self.min_pf)**2 - p_ach**2)) * numpy.sign(q_ach))
            # run function for ERM model type
            if self.model_type == 'ERM':
                
                response.P_injected_max = self.max_power_discharge
                response.Q_injected_max = float(numpy.sqrt(numpy.abs(self.max_apparent_power**2 - p_ach**2)) )  

                # Calculate SoC and Power Achieved
                Ppos = min(self.max_power_charge, max(p_ach, 0))
                Pneg = max(self.max_power_discharge, min(p_ach, 0))
                SoC[1] = SoC[0] + float(100) * dt * (Pneg + (
                    Ppos * self.energy_efficiency) + self.self_discharge_power) / self.energy_capacity
                if SoC[1] > self.max_soc:
                    Ppos = (self.energy_capacity * (self.max_soc - SoC[0]) / (
                        float(100) * dt) - self.self_discharge_power) / self.energy_efficiency
                    SoC[1] = self.max_soc
                    if SoC[0] == self.max_soc:
                        Ppos = 0
                if SoC[1] < self.min_soc:
                    Pneg = self.energy_capacity * (self.min_soc - SoC[0]) / (
                        float(100) * dt) - self.self_discharge_power
                    SoC[1] = self.min_soc
                    if SoC[0] == self.min_soc:
                        Pneg = 0

                p_ach = (Ppos + Pneg)*self.num_of_devices
                q_ach =  q_ach*self.num_of_devices

                response.P_injected = p_ach
                response.Q_injected = q_ach
                response.P_dot = p_ach-self.P_injected
                response.Q_dot = q_ach-self.Q_injected
                response.P_service = 0
                response.Q_service = 0
                response.P_service_max = 0
                response.Q_service_max = 0
                response.Loss_standby = self.self_discharge_power
                response.Eff_throughput = float(p_ach>0)*self.energy_efficiency + float(p_ach>0)

                self.soc = SoC[1]
                return response
            # run function for ERM model type
            elif self.model_type == 'CRM':
                
                # convert AC power p_ach to DC power pdc
                self.pdc = self.coeff_2*(p_ach**2)+self.coeff_1*(p_ach)+self.coeff_0 
                # convert DC power pdc to DC current
                """ self.ibat = self.pdc *1000 / self.vbat

                self.pdc = self.ibat * ((self.v1 + self.v2 + self.voc + self.ibat*self.r0) *self.n_cells) *1000

                0 = -self.pdc + (self.v1 + self.v2 + self.voc)*self.n_cells) *1000*self.ibat + self.r0 *self.n_cells*1000* (self.ibat**2) """

                b = ((self.v1 + self.v2 + self.voc)*self.n_cells) 
                a = self.r0 * self.n_cells 
                c = -self.pdc* 1000
                self.ibat = (-b+numpy.sqrt(b**2 - 4*a*c))/(2*a)

                self.vbat = (self.v1 + self.v2 + self.voc + self.ibat*self.r0) *self.n_cells

                # calculate dynamic voltages
                self.v1 = self.v1 + dt *( (1/(self.r1*self.c1))*self.v1 + (1/(self.c1))*self.ibat)
                self.v2 = self.v2 + dt *( (1/(self.r2*self.c2))*self.v1 + (1/(self.c2))*self.ibat)

            
                response.P_injected_max = self.max_power_discharge
                response.Q_injected_max = float(numpy.sqrt(numpy.abs(self.max_apparent_power**2 - p_ach**2))) 

                # Calculate SoC and Power Achieved
                Ipos = min(self.max_current_charge, max(self.ibat, 0))
                Ineg = max(self.max_current_discharge, min(self.ibat, 0))
                SoC[1] = SoC[0] + float(100) * dt * (Ineg + (
                    Ipos * self.coulombic_efficiency) + self.self_discharge_current) / self.charge_capacity
                if SoC[1] > self.max_soc:
                    Ipos = (self.charge_capacity * (self.max_soc - SoC[0]) / (
                        float(100) * dt) - self.self_discharge_current) / self.coulombic_efficiency
                    SoC[1] = self.max_soc
                    if SoC[0] == self.max_soc:
                        Ipos = 0
                    self.pdc  = Ipos *self.vbat / 1000
                    if self.coeff_2 != 0:
                        p_ach = (-self.coeff_1 +float(numpy.sqrt(self.coeff_1**2 - 4*self.coeff_2*(self.coeff_0-self.pdc))))/(2*self.coeff_2)
                    else: 
                        p_ach  = (self.pdc - self.coeff_0)/self.coeff_1
                if SoC[1] < self.min_soc:
                    Ineg = self.charge_capacity * (self.min_soc - SoC[0]) / (
                        float(100) * dt) - self.self_discharge_current
                    SoC[1] = self.min_soc
                    if SoC[0] == self.min_soc:
                        Ineg = 0
                    self.pdc  = Ineg *self.vbat / 1000
                    if self.coeff_2 != 0:
                        p_ach = (-self.coeff_1 +float(numpy.sqrt(self.coeff_1**2 - 4*self.coeff_2*(self.coeff_0-self.pdc))))/(2*self.coeff_2)
                    else: 
                        p_ach  = (self.pdc - self.coeff_0)/self.coeff_1

                self.ibat = Ipos + Ineg
                self.soc = SoC[1]
                self.voc_update()

                self.vbat = (self.v1 + self.v2 + self.voc + self.ibat*self.r0) *self.n_cells
                    
                p_ach =  p_ach*self.num_of_devices
                q_ach =  q_ach*self.num_of_devices

                response.P_injected = p_ach
                response.Q_injected = q_ach
                response.P_dot = p_ach-self.P_injected
                response.Q_dot = q_ach-self.Q_injected
                response.P_service = 0
                response.Q_service = 0
                response.P_service_max = 0
                response.Q_service_max = 0
                response.Loss_standby = self.self_discharge_current*(self.voc)
                response.E = (self.soc-self.min_soc) * self.charge_capacity * self.voc
                response.Eff_throughput =  (response.E - self.es)/(p_ach*dt)
                self.es = response.E
                self.vbat = (self.v1 + self.v2 + self.voc + self.ibat*self.r0) *self.n_cells

                return response
    
    def voc_update(self): 
        if self.voc_model_type== "Linear":
            self.voc = self.voc_model_m*self.soc + self.voc_model_b
        elif self.voc_model_type == "Quadratic":
            self.voc = self.voc_model_a*(self.soc**2) + self.voc_model_b*self.soc + self.voc_model_c
        elif self.voc_model_type == "Cubic":
            self.voc = self.voc_model_a*(self.soc**3) + self.voc_model_b*(self.soc**2) + self.voc_model_c*self.soc + self.voc_model_d
        elif self.voc_model_type == "CubicSpline":
            i = 0
            for s in self.voc_model_SoC_list:
                if self.soc > s:
                    i = i + 1
            self.voc = self.voc_model_a[i]*(self.soc**3) + self.voc_model_b[i]*(self.soc**2) + self.voc_model_c[i]*self.soc + self.voc_model_d[i]
        else:
            print('Error: open circuit voltage (voc) model type (voc_model_type) is not defined properly')
            print('in config_self.ini set VocModelType=Linear or =CubicSpline')
        pass

    def voc_query(self,SOC): 
        if self.voc_model_type== "Linear":
            VOC = self.voc_model_m*self.soc + self.voc_model_b
        elif self.voc_model_type == "Quadratic":
            VOC = self.voc_model_a*(self.soc**2) + self.voc_model_b*self.soc + self.voc_model_c
        elif self.voc_model_type == "Cubic":
            VOC = self.voc_model_a*(self.soc**3) + self.voc_model_b*(self.soc**2) + self.voc_model_c*self.soc + self.voc_model_d
        elif self.voc_model_type == "CubicSpline":
            i = 0
            for s in self.voc_model_SoC_list:
                if self.soc > s:
                    i = i + 1
            VOC = self.voc_model_a[i]*(self.soc**3) + self.voc_model_b[i]*(self.soc**2) + self.voc_model_c[i]*self.soc + self.voc_model_d[i]
        else:
            print('Error: open circuit voltage (voc) model type (voc_model_type) is not defined properly')
            print('in config_self.ini set VocModelType=Linear or =CubicSpline')
        return VOC

    def cost(self, initSoC = 50,finSoC = 50,dt = 1):
        import numpy
        # pre-define variables
        Cost = 0
        Able = 1
        Power = 0
        # impose SoC constraints
        if initSoC > self.max_soc:
            Able = 0
        if initSoC < self.min_soc:
            Able = 0
        if finSoC > self.max_soc:
            Able = 0
        if finSoC < self.min_soc:
            Able = 0

        if self.model_type == 'ERM':
            DSoC = finSoC - initSoC
            if DSoC >= 0:
                Power = ((self.energy_capacity * DSoC / (float(100)*dt)) - self.self_discharge_power)/self.energy_efficiency
            if DSoC < 0:
                Power = (self.energy_capacity * DSoC / (float(100)*dt)) - self.self_discharge_power
            # linear power cost function
        #     Cost = Power*0.01
            # quadratic power cost function
        #     Cost = Power*Power*0.01
            Ppos = max(Power,0)
            Pneg = min(Power,0)
            # inpose power constraints
            if Ppos > self.max_power_charge:
                Able = 0
                Power = 0
            if Pneg < self.max_power_discharge:
                Able = 0
                Power = 0
        if self.model_type == 'CRM':
            Current = 0
            DSoC = finSoC - initSoC
            # Calculate battery current
            if DSoC >= 0:
                Current = ((self.charge_capacity * DSoC / (float(100)*dt)) - self.self_discharge_current)/self.coulombic_efficiency
            if DSoC < 0:
                Current = ((self.charge_capacity * DSoC / (float(100)*dt)) - self.self_discharge_current)
            Voltage = self.n_cells*(Current*self.r0+((self.voc_query(initSoC)+self.voc_query(finSoC))/2))
            PowerDC =  Current*(Voltage)/1000
            if self.coeff_2 != 0:
                Power = (-self.coeff_1 +float(numpy.sqrt(self.coeff_1**2 - 4*self.coeff_2*(self.coeff_0-PowerDC))))/(2*self.coeff_2)
            else: 
                Power  = (PowerDC - self.coeff_0)/self.coeff_1

            Ipos = max(Current,0)
            Ineg = min(Current,0)
            # impose current limites
            if Ipos > self.max_current_charge:
                Able = 0
                Power = 0
                Current = 0
            if Ineg < self.max_current_discharge:
                Able = 0
                Power = 0
                Current = 0
            # impose voltage limites
            if Voltage > self.max_voltage:
                Voltage = self.max_voltage
                Able = 0
                Power = 0
                Current = 0
            if Voltage < self.min_voltage:
                Voltage = self.min_voltage
                Able = 0
                Power = 0
                Current = 0 
                
            Ppos = max(Power,0)
            Pneg = min(Power,0)
            # impose power limits
            if Ppos > self.max_power_charge:
                Able = 0
                Power = 0
                Current = 0
            if Pneg < self.max_power_discharge:
                Able = 0
                Power = 0
                Current = 0

        Power = Power*self.num_of_devices
        Cost = Power*self.num_of_devices
        return [Power,Cost,Able]#Power,Cost,Able

    def forecast(self, requests):
        """
        Forecast feature

        :param fleet_requests: list of fleet requests

        :return res: list of service responses
        """
        responses = []
        SOC = self.soc 

        if self.model_type == 'ERM':
            # Iterate and process each request in fleet_requests
            for req in requests:
                FleetResponse = self.run(req.P_req,req.Q_req,self.soc ,req.sim_step)
                res = FleetResponse
                responses.append(res)
            # reset the model
            self.soc = SOC 
            
        elif self.model_type == 'CRM':
            PDC = self.pdc 
            IBAT = self.ibat
            VBAT = self.vbat
            V1 = self.v1
            V2 = self.v2
            VOC = self.voc 
            ES = self.es
            # Iterate and process each request in fleet_requests
            for req in requests:
                FleetResponse = self.run(req.P_req,req.Q_req,self.soc,req.sim_step)
                res = FleetResponse
                responses.append(res)
            # reset the model
            self.soc = SOC 
            self.pdc = PDC
            self.ibat = IBAT
            self.vbat = VBAT
            self.v1 = V1
            self.v2 = V2
            self.voc = VOC
            self.es = ES
        else: 
            print('Error: ModelType not selected as either energy reservoir model (self), or charge reservoir model (self)')
            print('Battery-Inverter model forecast is unable to continue. In config.ini, set ModelType to self or self')

        return responses

    def change_config(self, fleet_config):
        """
        :param fleet_config: an instance of FleetConfig
        """

        # change config

        pass


if __name__ == '__main__':
    fleet = BatteryInverterFleet()
    print(fleet.name)
    print(fleet.model_type)
