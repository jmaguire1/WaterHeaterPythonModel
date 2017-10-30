# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling fleet of water heaters
@author: cbooten
"""
import numpy as np
import matplotlib.pyplot as plt

from simple_wh_cwb_2 import ChuckWaterHeater
import random

def main():
    numWH = 1 #number of water heaters in fleet
    TtankInitialMean = 125 #deg F
    TtankInitialStddev = 5 #deg F
    TsetInitialMean = 125 #deg F
    TsetInitialStddev = 5 #deg F
    
    # for capacity, type and location need to specify discrete values and sample in such a way as to get overall distribution that I want 
    CapacityMasterList = [50,50,50,50,50,50,50,50,40,40,80] #70% 50 gal, 20% 40 gal, 10% 80 gal
    TypeMasterList = ['ER','ER','ER','ER','ER','ER','ER','ER','ER','HP'] #elec_resis 90% and HPWH 10%
    LocationMasterList =['Conditioned','Conditioned','Conditioned','Conditioned','Unconditioned'] #80% conditioned, 20% unconditioned
    HotDrawMasterList = [1.5,1.1,0.7,0.2,0.05,0.05,0.02,0.01,0.01,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#sample hourly draw pattern. will randomly sample this 
    # 1x for each house and assume pattern is the same for that house for the entire year
    
        
        
    # define annual load service request 
    fleet_load_request = []
#    fleet_regulation_request = []
    for hour in range(8760):
        magnitude_load_add_shed = 2e6 + 1e6*random.random() #def magnitude of request for load add/shed
        if hour % 12 == 0 or hour % 12 == 1 or hour % 12 == 2:
            service = ['load shed',magnitude_load_add_shed]
        elif hour % 7 == 0 or hour % 7 == 1:
            service = ['load add',magnitude_load_add_shed]
        else:
            service = ['none',0]
            
        fleet_load_request.append(service)
        
    
    
#    #define regulation request separately since timescale is very different
#    for second in range(1000):
#        magnitude_regulation = 5e4 + 1e5*random.random() #def magnitude of request for regulation
#        if second % 4 == 0: #send a new signal every 4 seconds
#            service =['regulation',magnitude_regulation]
#        else:
#            service =['none',0]
#            
#        fleet_regulation_request.append(service)
    
#    print(fleet_regulation_request[0:5])
    #print(fleet_request)
    
   ############################################################################# 
#    1) generate distribution of initial WH fleet states. this means Ttank, Tset, capacity, location (cond/uncond), type (elec resis or HPWH).
#    autogenerate water draw profile for the yr for each WH in fleet, this will be imported later, just get something reasonable here
    TtankInitial=np.random.normal(TtankInitialMean, TtankInitialStddev,numWH)
    TsetInitial=np.random.normal(TsetInitialMean, TsetInitialStddev,numWH)
    

    Capacity = [random.choice(CapacityMasterList) for n in range(numWH)]
    Type = [random.choice(TypeMasterList) for n in range(numWH)]
    Location = [random.choice(LocationMasterList) for n in range(numWH)]
    Hot_draw = np.array([[random.choice(HotDrawMasterList) for h in range(24)] for i in range(numWH)])
    
    (Tamb, RHamb, Tmains, hot_draw) = get_annual_conditions()
    
#    plt.figure(1)
#    plt.clf()
#    plt.hist(TsetInitial)  
#    
#    
#    plt.figure(2)
#    plt.clf()
#    plt.plot(Hot_draw[4,:])
#    
#    print(Location[1:100])
    
    ###########################################################################    
    #3) at each timestep, rank fleet by:  available capacity and SoC and some algorithm for selecting units with minimum # of service calls). 
    
    
    
    #       goal is to optimize for calling WH with greatest availability but minimum number of calls. unsure exact form of algorithm.
    #5) add the load and regulation requests to get a single request
    #6) apply request down the ranked list until is satisfied
    
    Tset = [[0 for x in range(8760)] for y in range(numWH)]
    Ttank = [[0 for x in range(8760)] for y in range(numWH)]
#    Eused = []
#    Eloss = []
#    ElementOn = []
#    Eservice = []
    SoC = [[0 for x in range(8760)] for y in range(numWH)]
    AvailableCapacity = [[0 for x in range(8760)] for y in range(numWH)]
    ServiceCallsAccepted = [[0 for x in range(8760)] for y in range(numWH)]
    MaxServiceCalls = [0  for y in range(numWH)]
#    wh_attributes = [[0 for x in range(8760)] for y in range(numWH)]
    
        
#            if hour == 1: #assign initial values TtankInitial, TsetInitial, and WH characteristics: Capacity, Type, Location and Hot_draw
    whs = [ChuckWaterHeater(TsetInitial[number], Tamb[1], RHamb[1], Tmains[1], Hot_draw[number,1], fleet_load_request[1], Capacity[number], Type[number], Location[number], 0, MaxServiceCalls[number]) for number in range(numWH)]
#                tset, ttank, eused, eloss, elementOn, eservice, soC, availableCapacity = wh.execute()
#            else:
#                wh = ChuckWaterHeater(wh_attributes[number,hour-1], Tamb[hour], RHamb[hour], Tmains[hour], Hot_draw[number,hour], fleet_load_request[hour], Ttank[number,hour -1], Capacity[number], Type[number], Location[number])
                
    for hour in range(7):    
        number = 0
#        print(hour)
        for wh in whs: #numWH
            if hour == 0:
                ttank, tset, soC, availableCapacity, serviceCallsAccepted = wh.execute(TsetInitial[number], Tamb[0], RHamb[0], Tmains[0], Hot_draw[number,0], fleet_load_request[0], TtankInitial[number])
                print('tank initial', TtankInitial[number])
            else:
                lastHour = hour - 1
                TsetLast = Tset[number][lastHour]
                TtankLast = Ttank[number][lastHour]-5*hour
                HourOfDay = hour % 24
#                print(Hot_draw[number,HourOfDay])
                print(TtankLast, hour)
                ttank, tset, soC, availableCapacity, serviceCallsAccepted = wh.execute(TsetLast, Tamb[hour], RHamb[hour], Tmains[hour], Hot_draw[number,HourOfDay], fleet_load_request[hour], TtankLast)
#                print(ttank)
                
            
#            print(Ttank[number][hour])
            
            Tset[number][hour] = tset
            Ttank[number][hour] = ttank
#            print(Tset[number][hour])
            SoC[number][hour] = soC
            AvailableCapacity[number][hour] = availableCapacity
            ServiceCallsAccepted[number][hour] = serviceCallsAccepted
            number += 1
        #analysis   
#        for wh in whs:
#            wh_thistory[wh,:] = np.array(wh.temp_history)  
            
                
                
    
#    print(len(Ttank))
    print(Ttank[0][0:2])
       
    
    
    
#    wh = ChuckWaterHeater(control_signal=control)
#    Ttank, Eused, Eloss, ElementOn, Eservice = wh.execute_year()
    # print(Ttank[1:50], Eused[1:50], Eloss[1:50], control[1:50])
    
    
#    plt.figure(1)
#    plt.clf()
#    plt.plot(Ttank[1:10][20])
#    
#    plt.figure(2)
#    plt.clf()
#    plt.plot(SoC[1:10][20])
#    plt.show()
    
#    return Ttank, Eused, Eloss, ElementOn, Eservice



def get_annual_conditions():
        Tamb = []
        RHamb = []
        Tmains = []
        hot_draw = []
        
        for hour in range(8760):
            if hour >  4000:   
                Tamb.append(65) # deg F
                RHamb.append(30) #%
                Tmains.append(55) # deg F
            else:
                Tamb.append(45) # deg F
                RHamb.append(40) #%
                Tmains.append(40) # deg F
            if hour % 5 == 0: #if hour is divisible by 5
                hot_draw.append(0.5) #gpm
            else:
                hot_draw.append(0)
   
        return Tamb, RHamb, Tmains, hot_draw
# take individual water heater and vary inputs for water draw event schedule,
# Tambient based on season for conditioned and unconditioned space,
# setpoint temperature, tank capacity, heat pump vs. electric resistance, if heat pump
# need a distribution of COP

#will need to add manufacturer control/protection logic to waterHeater model
# specify max number of grid service responses for various timescales (i.e. 2x per day and 20 times per month for example) 
# this could be a function of service type. for load shed it could be 1x/day, for regulation might be participate for 30min/day
# specify multiple levels of load add/shed? maybe unnessary since aggregating devices first?

# will need to assume some sort of control signal/request: regulation, load add, load shed for now. 
# each device will decide if it can provide the service????? then see if service provided matches up with SoC for fleet???? 

# run N water heaters, then convert to battery equivalent model terminology, need Energy storage capacity and SoC, 
# elec resistance or HPWH (input into WH model), conditioned or unconditioned space (input into WH model), elec energy used, 
# thermal energy delivered, tank energy loss, parasitic energy

# fleet storage capacity, Storage_capacity_fleet = sum of individual capacity with Tmax and Tmin defined, m_water_in_tank*heat capacitance*(Tmax-Tmin)

# fleet state of charge, SoC_fleet = (sum of SoC_individual*Capacity_individual) / sum(Capacity_individual)

# Elec Power to end use (i.e. elec power required to deliver hot water) = sum(electrical power input per device)

# fleet parasitic power = sum(tank losses+parasitic elec power) 

if __name__ == '__main__':
    main()