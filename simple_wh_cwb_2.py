# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 08:38:56 2017
super simple water heater model
@author: cbooten
"""



class ChuckWaterHeater():
    def __init__(self, Tset = 125, Tamb = 50, RHamb= 45, Tmains = 50, hot_draw = 0, control_signal = 'none', Capacity = 50, Type = 'ER', Location = 'Conditioned', service_calls_accepted = 0, max_service_calls = 100):
        #Declare constants
        self.Tset = Tset #F, specified so fleet can have a distribution of initial conditions
        self.Tdeadband = 10 #delta F
        self.E_heat = 4.5 #kW
        self.UA = 1 #W/K
        self.control = control_signal
        self.Tmin = 105 # deg F
        self.Tmax = 160 # deg F
#        self.Ttank = Ttank #deg F, specified so fleet can have a distribution of initial conditions
#        print('ttank', Ttank)
        self.Tamb = Tamb#deg F, specified so fleet can have a distribution of initial conditions
        self.RHamb = RHamb# %, specified so fleet can have a distribution of initial conditions
        self.Tmains = Tmains#deg F, specified so fleet can have a distribution of initial conditions
        self.hot_draw = hot_draw#gpm, specified so fleet can have a distribution of initial conditions
        self.Capacity = Capacity # gallons
        self.service_calls_accepted = int(service_calls_accepted)
        self.max_service_calls = int(max_service_calls)
        
    def execute(self, Tset, Tamb, RHamb, Tmains, hot_draw, control_signal, Ttank):
        Element_on = 0
#        self.Ttank = Ttank #deg F, specified so fleet can have a distribution of initial conditions
        (Tset, Ttank, Eused, Eloss, ElementOn, Eservice, SoC, AvailableCapacity, service_calls_accepted) = self.WH(self.Tset, Ttank,self.Tamb,self.Tmains,self.hot_draw, self.control, Element_on, self.service_calls_accepted, self.max_service_calls)
        
        return Tset, Ttank, SoC, AvailableCapacity, service_calls_accepted

    
    def WH(self,Tset_ts, Tlast,Tamb_ts,Tmains_ts,hot_draw_ts, control_signal_ts, Element_on_ts, service_calls_accepted_ts, max_service_calls):
        """ Calculate next temperature and load"""
         
        if Tlast < self.Tset - self.Tdeadband:
            Eused_ts = self.E_heat*1000 #kW used
            Element_on_ts = 1
        elif Element_on_ts == 1 and Tlast< self.Tset:
            Eused_ts = self.E_heat*1000 #kW used
            Element_on_ts = 1
        else:
            Eused_ts = 0
            Element_on_ts = 0
            
        #modify operation based on control signal    
        Eused_baseline_ts = Eused_ts # get baseline energy use w/o providing grid service
        
        if control_signal_ts  == 'load shed' and Tlast > self.Tmin and max_service_calls > service_calls_accepted_ts:
            Eused_ts = 0
            Element_on_ts = 0
            service_calls_accepted_ts += 1
        elif control_signal_ts  == 'load shed' and Tlast < self.Tmin:
            # don't change anything
            Eused_ts = Eused_ts
            Element_on_ts = Element_on_ts
        elif control_signal_ts  == 'load add' and Tlast > self.Tmax:
            Eused_ts = 0 #make sure it stays off
            Element_on_ts = 0
        elif control_signal_ts  == 'load add' and Tlast < self.Tmax and max_service_calls > service_calls_accepted_ts:
            #make sure it stays on
            Eused_ts = self.E_heat*1000 #kW used
            Element_on_ts = 1
            service_calls_accepted_ts += 1
        
        #calculate energy provided as a service
        Eservice_ts = Eused_ts-Eused_baseline_ts
        
        #could change this at some point based on signals
        Tset_ts = self.Tset
            
        Eloss_ts = self.UA*(Tlast-Tamb_ts)    
        Ttank_ts = Tlast + (Eused_ts - Eloss_ts)*3600/(180*4810) + (1 + hot_draw_ts*60/50*(Tmains_ts - Tlast)) 
        print('tlast', Tlast)
        #3600 converts W to Whrs, 180 is kg of water in 50ga tank, 4810 is heat cap of water
        # second expression in line above is new mixed temperature due to water draw only
        
        SOC = (Ttank_ts - self.Tmin)/(self.Tmax - self.Tmin)
        isAvailable = 1 if max_service_calls-service_calls_accepted_ts > 0 else 0
        Available_Capacity = SOC*self.Capacity/3.79*4180*(self.Tmax - self.Tmin)*isAvailable #Joules, 3.79 = kg/gal, 4180 heat cap of water J/kgK
        
        return Tset_ts, Ttank_ts, Eused_ts, Eloss_ts, Element_on_ts, Eservice_ts, SOC, Available_Capacity, service_calls_accepted_ts
    
#if __name__ == '__main__':
#    main()