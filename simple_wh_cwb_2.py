# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 08:38:56 2017
super simple water heater model
@author: cbooten
"""



class ChuckWaterHeater():
    def __init__(self, Tamb = 50, RHamb= 45, Tmains = 50, hot_draw = 0, control_signal = 'none', Capacity = 50, Type = 'ER', Location = 'Conditioned', service_calls_accepted = 0, max_service_calls = 100):
        #Declare constants
        self.Tdeadband = 1 #delta F
        self.E_heat = 4.5 #kW
        self.UA = 20 #W/K
#        self.control = control_signal
        self.Tmin = 105 # deg F
        self.Tmax = 160 # deg F
#        self.Tamb = Tamb#deg F, specified so fleet can have a distribution of initial conditions
#        self.RHamb = RHamb# %, specified so fleet can have a distribution of initial conditions
#        self.Tmains = Tmains#deg F, specified so fleet can have a distribution of initial conditions
#        self.hot_draw = hot_draw#gpm, specified so fleet can have a distribution of initial conditions
        self.Capacity = Capacity # gallons
#        self.service_calls_accepted = int(service_calls_accepted)
        self.max_service_calls = int(max_service_calls)

        
    def execute(self,Ttank, Tset, Tamb, RHamb, Tmains, hot_draw, control_signal, service_calls_accepted):
        Element_on = 0

        (Ttank, Tset, Eused, Eloss, ElementOn, Eservice, SoC, AvailableCapacity, service_calls_accepted) = self.WH(Tset, Ttank,Tamb,Tmains,hot_draw, control_signal, Element_on, service_calls_accepted, self.max_service_calls)
        
        return Ttank, Tset, SoC, AvailableCapacity, service_calls_accepted, Eservice

    
    def WH(self,Tset, Tlast,Tamb_ts,Tmains_ts,hot_draw_ts, control_signal_ts, Element_on_ts, service_calls_accepted_ts, max_service_calls):
        """ Calculate next temperature and load"""
         
        Eloss_ts = self.UA*(Tlast-Tamb_ts)    
        dT_from_hot_draw = hot_draw_ts*60/50*(Tlast - Tmains_ts)
        dT_loss = Eloss_ts*3600/(180*4810)
        
        if Tlast < Tset - self.Tdeadband:
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
#        print(Tlast,self.Tmin, max_service_calls, service_calls_accepted_ts )
        if control_signal_ts[0]  == 'load shed' and Tlast > self.Tmin and max_service_calls > service_calls_accepted_ts and Element_on_ts == 1: #Element_on_ts = 1 requirement eliminates free rider situation
            Eused_ts = 0
            Element_on_ts = 0
            service_calls_accepted_ts += 1
#            print('shed','tlast=',Tlast,'tmin=', self.Tmin,'max calls=',max_service_calls,'calls accepted=',service_calls_accepted_ts)
        elif control_signal_ts[0]  == 'load shed' and Tlast < self.Tmin:
            # don't change anything
            Eused_ts = Eused_ts
            Element_on_ts = Element_on_ts
        elif control_signal_ts[0]  == 'load add' and Tlast > self.Tmax:
            Eused_ts = 0 #make sure it stays off
            Element_on_ts = 0
        elif control_signal_ts[0]  == 'load add' and Tlast < self.Tmax and max_service_calls > service_calls_accepted_ts and Element_on_ts == 0: #Element_on_ts = 0 requirement eliminates free rider situation
            #make sure it stays on
            Eused_ts = self.E_heat*1000 #kW used
            Element_on_ts = 1
            service_calls_accepted_ts += 1
#            print('add','tlast',Tlast,'tmax=', self.Tmax,'max calls=',max_service_calls,'calls accepted=',service_calls_accepted_ts)
        
        #calculate energy provided as a service, >0 is load add, <0 load shed
        # if the magnitude of the service that could be provided is greater than what is requested, just use what is requested and adjust the element on time
#        print('Available',abs(Eused_ts-Eused_baseline_ts), 'requested',control_signal_ts[1])
        if abs(Eused_ts-Eused_baseline_ts) > abs(control_signal_ts[1]): 
            Eservice_ts = control_signal_ts[1]
            Eused_ts = control_signal_ts[1] + Eused_baseline_ts
            Element_on_ts = control_signal_ts[1]/(Eused_ts-Eused_baseline_ts)
        else: # assumes WH can't meet the entire request so it just does as much as it can
            Eservice_ts = Eused_ts-Eused_baseline_ts
#        print('provided',Eservice_ts)
        #could change this at some point based on signals
        Tset_ts = Tset
#        print(service_calls_accepted_ts)    
        
        dT_power_input = Eused_ts*3600/(180*4810)
        Ttank_ts = Tlast + dT_power_input - dT_loss - dT_from_hot_draw 
        #3600 converts W to Whrs, 180 is kg of water in 50ga tank, 4810 is heat cap of water
        # second expression in line above is new mixed temperature due to water draw only
        
        SOC = (Ttank_ts - self.Tmin)/(self.Tmax - self.Tmin)
#        isAvailable = 1 if max_service_calls-service_calls_accepted_ts > 0 else 0
        Available_Capacity = abs(Eused_ts-Eused_baseline_ts) #SOC*self.Capacity/3.79*4180*(self.Tmax - self.Tmin)*isAvailable #Joules, 3.79 = kg/gal, 4180 heat cap of water J/kgK
        
        return Ttank_ts, Tset_ts, Eused_ts, Eloss_ts, Element_on_ts, Eservice_ts, SOC, Available_Capacity, service_calls_accepted_ts
    
if __name__ == '__main__':
    main()