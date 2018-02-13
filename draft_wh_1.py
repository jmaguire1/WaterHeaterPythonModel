# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 08:38:56 2017
super simple water heater model
@author: chuck booten, jeff maguire, xin jin
"""



class WaterHeater():
    def __init__(self, Tamb = 50, RHamb= 45, Tmains = 50, hot_draw = 0, control_signal = 'none', Capacity = 50, Type = 'ER', Location = 'Conditioned', service_calls_accepted = 0, max_service_calls = 100, time_step = 60):
        #Declare constants
        self.Tdeadband = 1 #delta F
        self.E_heat = 4.5 #kW
        self.UA = 10 #W/K
        self.Tmin = 105 # deg F
        self.Tmax = 160 # deg F
        self.Capacity = Capacity # gallons
        self.max_service_calls = int(max_service_calls)

        
    def execute(self,Ttank, Tset, Tamb, RHamb, Tmains, hot_draw, control_signal, service_calls_accepted, Element_on, timestep):
        (Ttank, Tset, Eused, Eloss, ElementOn, Eservice, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, is_available) = self.WH(Ttank, Tset,Tamb,Tmains,hot_draw, control_signal, Element_on, service_calls_accepted, self.max_service_calls, timestep)
        
        return Ttank, Tset, SoC, AvailableCapacityAdd, AvailableCapacityShed, service_calls_accepted, Eservice, is_available, ElementOn
        
    def WH(self,Tlast, Tset, Tamb_ts,Tmains_ts,hot_draw_ts, control_signal_ts, Element_on_ts, service_calls_accepted_ts, max_service_calls, timestep):
#############################################################################
        #        Baseline operation
        Eloss_ts = self.UA*(Tlast-Tamb_ts)    
        dT_from_hot_draw = (hot_draw_ts)/self.Capacity*(Tlast - Tmains_ts)# hot_draw is in gal for the timestep
        dT_loss = Eloss_ts*timestep*60/(3.79*self.Capacity*4810) #3.79 kg/gal of water, 4810 is J/kgK heat capacity of water, timestep units are minutes
        
        if Tlast < Tset - self.Tdeadband:
            Eused_baseline_ts = self.E_heat*1000 #W used
            Element_on_ts = 1
        elif Element_on_ts == 1 and Tlast < Tset + self.Tdeadband:
            Eused_baseline_ts = self.E_heat*1000 #W used
            Element_on_ts = 1
        else:
            Eused_baseline_ts = 0
            Element_on_ts = 0
            
  ###########################################################################          
        #modify operation based on control signal    
        if control_signal_ts[1]  < 0 and Tlast > self.Tmin and max_service_calls > service_calls_accepted_ts and Element_on_ts == 1: #Element_on_ts = 1 requirement eliminates free rider situation
            Eused_ts = 0 #make sure it stays off
            Element_on_ts = 0
            service_calls_accepted_ts += 1
        elif control_signal_ts[1]  < 0 and Tlast < self.Tmin:
            # don't change anything
            Eused_ts = Eused_baseline_ts
        elif control_signal_ts[1]  > 0 and Tlast > self.Tmax:
            Eused_ts = 0 #make sure it stays off
            Element_on_ts = 0
        elif control_signal_ts[1]  > 0 and Tlast < self.Tmax and max_service_calls > service_calls_accepted_ts and Element_on_ts == 0: #Element_on_ts = 0 requirement eliminates free rider situation
            #make sure it stays on
            Eused_ts = self.E_heat*1000 #W used
            Element_on_ts = 1
            service_calls_accepted_ts += 1
        else:#no changes
            Eused_ts = Eused_baseline_ts
        
        #calculate energy provided as a service, >0 is load add, <0 load shed
        # if the magnitude of the service that could be provided is greater than what is requested, just use what is requested and adjust the element on time
#        print('Available',abs(Eused_ts-Eused_baseline_ts), 'requested',control_signal_ts[1])
        if abs(Eused_ts-Eused_baseline_ts) > abs(control_signal_ts[1]): 
            Eservice_ts = control_signal_ts[1]
            Eused_ts = control_signal_ts[1] + Eused_baseline_ts
            Element_on_ts = control_signal_ts[1]/(Eused_ts-Eused_baseline_ts)
        else: # assumes WH can't meet the entire request so it just does as much as it can
            Eservice_ts = Eused_ts-Eused_baseline_ts
        #could change this at some point based on signals
        Tset_ts = Tset
        
        dT_power_input = Eused_ts*timestep*60/(3.79*self.Capacity*4810)#timestep is in minutes so mult by 60 to get seconds
        Ttank_ts = Tlast + dT_power_input - dT_loss - dT_from_hot_draw 
    
#        Calculate more parameters to be passed up
        SOC = (Ttank_ts - self.Tmin)/(self.Tmax - self.Tmin)
        isAvailable_ts = 1 if max_service_calls > service_calls_accepted_ts  else 0
        Available_Capacity_Add = (1-SOC)*self.Capacity*3.79*4180*(self.Tmax - self.Tmin)*isAvailable_ts/(timestep*60) #/timestep converts from Joules to Watts, 3.79 = kg/gal, 4180 heat cap of water J/kgK
        Available_Capacity_Shed = SOC*self.Capacity*3.79*4180*(self.Tmax - self.Tmin)*isAvailable_ts/(timestep*60) #/timestep*60 converts from Joules to Watts,
        
        return Ttank_ts, Tset_ts, Eused_ts, Eloss_ts, Element_on_ts, Eservice_ts, SOC, Available_Capacity_Add, Available_Capacity_Shed, service_calls_accepted_ts, isAvailable_ts
    
if __name__ == '__main__':
    main()