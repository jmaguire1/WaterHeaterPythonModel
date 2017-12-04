# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling fleet of water heaters
@author: cbooten
"""
import numpy as np
import matplotlib.pyplot as plt

from simple_wh_cwb_3 import ChuckWaterHeater
import random

def main():
    numWH = 100 #number of water heaters in fleet
    RunHours = 8760 #num hours in simulation
    TtankInitialMean = 125 #deg F
    TtankInitialStddev = 5 #deg F
    TsetInitialMean = 125 #deg F
    TsetInitialStddev = 5 #deg F
    minSOC = 0.2 # minimum SoC for aggregator to call for a service
    
    # for capacity, type and location need to specify discrete values and sample in such a way as to get overall distribution that I want 
    CapacityMasterList = [50,50,50,50,50,50,50,50,40,40,80] #70% 50 gal, 20% 40 gal, 10% 80 gal
    TypeMasterList = ['ER','ER','ER','ER','ER','ER','ER','ER','ER','HP'] #elec_resis 90% and HPWH 10%
    LocationMasterList =['Conditioned','Conditioned','Conditioned','Conditioned','Unconditioned'] #80% conditioned, 20% unconditioned
    HotDrawMasterList = [0.2,0.15,0.1, 0.1, 0.05,0.05,0.02,0.01,0.01,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#sample hourly draw pattern. will randomly sample this 
    # 1x for each house and assume pattern is the same for that house for the entire year
    MaxServiceCallMasterList = [100,80,80, 200, 150, 110, 50, 75, 100]
    
        
        
    # define annual load service request 
    fleet_load_request = []
    fleet_load_request_total = []
#    fleet_regulation_request = []
    for hour in range(RunHours):
        magnitude_load_add_shed = (7e4 + 2e4*random.random())/(numWH/1) #def magnitude of request for load add/shed, assume only 50% of WH will be able to respond so request "too much" load effectively
        if hour % 12 == 0 or hour % 12 == 1 or hour % 12 == 2:
            if hour > 1:
                service = ['load shed',-magnitude_load_add_shed]
                s = -magnitude_load_add_shed * numWH / 1
            else:
                service = ['none',0]
                s=0
        elif hour % 7 == 0 or hour % 7 == 1:
            service = ['load add',magnitude_load_add_shed]
            s = magnitude_load_add_shed * numWH / 1
        else:
            service = ['none',0]
            s=0
        
        fleet_load_request_total.append(s)
        fleet_load_request.append(service)
#        print(fleet_load_request[hour][1])
    
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
    MaxServiceCalls = [random.choice(MaxServiceCallMasterList) for n in range(numWH)]
    
#    print(MaxServiceCalls)
    
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
    
    Tset = [[0 for x in range(RunHours)] for y in range(numWH)]
    Ttank = [[0 for x in range(RunHours)] for y in range(numWH)]
    SoC = [[0 for x in range(RunHours)] for y in range(numWH)]
    AvailableCapacity = [[0 for x in range(RunHours)] for y in range(numWH)]
    ServiceCallsAccepted = [[0 for x in range(RunHours)] for y in range(numWH)]
    ServiceProvided = [[0 for x in range(RunHours)] for y in range(numWH)]
    IsAvailable = [[0 for x in range(RunHours)] for y in range(numWH)]
    TotalServiceProvidedPerWH = [0 for y in range(numWH)]
    TotalServiceProvidedPerTimeStep = [0 for y in range(RunHours)]
    TotalServiceCallsAcceptedPerWH = [0 for y in range(numWH)]
#    TotalServiceProvided = [0 for y in range(numWH)]

    whs = [ChuckWaterHeater(Tamb[1], RHamb[1], Tmains[1], Hot_draw[number,1], fleet_load_request[1], Capacity[number], Type[number], Location[number], 0, MaxServiceCalls[number]) for number in range(numWH)]
               
    for hour in range(RunHours):    
        number = 0
        servsum = 0
        capsum = 0
        request = 0
        NumDevicesToCall = 0
        lastHour = hour - 1
        if hour > 0:
#            print(fleet_load_request[hour])
            #decision making about which WH to call on for service, check if available at last hour, if so then 
            # check for SoC > X%, whatever number that is, divide the total needed and ask for that for each
            for n in range(numWH):
                if IsAvailable[n][lastHour] > 0 and SoC[n][lastHour] > minSOC:
                    NumDevicesToCall += 1
            
    #                    print('num devices',NumDevicesToCall,'is avail',IsAvailable[n][lastHour],'soc',SoC[n][lastHour])
            if fleet_load_request[hour][1] < 0 and NumDevicesToCall > 0: #if shed is called for and there are some devices that can respond
                newrequest = fleet_load_request_total[hour] / (NumDevicesToCall/(9.5*np.exp(-numWH/20)+1)) #9.5*exp(-numWH/20)+1 ad hoc curve fit based on trying numWH = 20,30,10,200 and doing hand curve fit. NOTE: THIS IS FOR UA = 30, COULD CHANGE IF THIS IS CHANGED
            elif fleet_load_request[hour][1] > 0 and NumDevicesToCall > 0: # easier to do load add, but some "available" devices still won't be able to respond so ask for extra 
                newrequest = fleet_load_request_total[hour] / (NumDevicesToCall/(9.5*np.exp(-numWH/20)+1)) #9.5*exp(-numWH/20)+1 ad hoc curve fit based on trying numWH = 20,30,10,200 and doing hand curve fit. 
                newrequest = fleet_load_request_total[hour] / (NumDevicesToCall/2)
            else:
                newrequest = fleet_load_request_total[hour]
                
            fleet_load_request[hour] = [fleet_load_request[hour][0],newrequest]
#            print(fleet_load_request[hour])
#            print('num devices',NumDevicesToCall)
        for wh in whs: #numWH
            if hour == 0:
                ttank, tset, soC, availableCapacity, serviceCallsAccepted, eservice, isAvailable = wh.execute(TtankInitial[number], TsetInitial[number], Tamb[0], RHamb[0], Tmains[0], Hot_draw[number,0], fleet_load_request[0], 0)
#                print('WH num',number,'tank',ttank,'soc',soC,'calls accepted', serviceCallsAccepted,'available?',isAvailable,'request',fleet_load_request[0])
            else:
                
                TsetLast = Tset[number][lastHour]
                TtankLast = Ttank[number][lastHour]
#                print(TtankLast)
                HourOfDay = hour % 24
                
                ttank, tset, soC, availableCapacity, serviceCallsAccepted, eservice, isAvailable = wh.execute(TtankLast, TsetLast, Tamb[hour], RHamb[hour], Tmains[hour], Hot_draw[number,HourOfDay], fleet_load_request[hour],  ServiceCallsAccepted[number][lastHour])
#                print('WH num',number,'tank',ttank,'soc',soC,'calls accepted', serviceCallsAccepted,'available?',isAvailable,'request',fleet_load_request[hour])
#                print('request',fleet_load_request[hour],'service',eservice)
            Tset[number][hour] = tset
#            print('provided',eservice)
            Ttank[number][hour] = ttank
            SoC[number][hour] = soC
            IsAvailable[number][hour] = isAvailable
            AvailableCapacity[number][hour] = availableCapacity
            capsum += availableCapacity
            ServiceCallsAccepted[number][hour] = serviceCallsAccepted
            ServiceProvided[number][hour] = eservice
            servsum += eservice
            TotalServiceProvidedPerWH[number] = TotalServiceProvidedPerWH[number] + ServiceProvided[number][hour]
#            print('number',number,'hr',hour,TotalServiceProvidedPerWH)
#            print('provided per hr',servsum)
            request += fleet_load_request[hour][1] 
            number += 1
        TotalServiceProvidedPerTimeStep[hour] += servsum #ServiceProvided[number][hour]
#    print('ttank',Ttank[0:20][1])
#    print(number)
#        print('hr',hour,'provided',TotalServiceProvidedPerTimeStep[hour],'request',request,'available',capsum)
#            print(Ttank[number][hour])
            
#    print(ServiceCallsAccepted)
#    print(TotalServiceProvidedPerTimeStep)
    
    for n in range(number):
        TotalServiceCallsAcceptedPerWH[n] = ServiceCallsAccepted[n][hour]
#        TotalServiceProvided[n] = ServiceProvided[n][hour]
#        print(ServiceProvided[n][hour])
        #analysis   
#        for wh in whs:
#            wh_thistory[wh,:] = np.array(wh.temp_history)  
            
                
#    print(Ttank[0][0:2])
       
    
    
    
#    wh = ChuckWaterHeater(control_signal=control)
#    Ttank, Eused, Eloss, ElementOn, Eservice = wh.execute_year()
    # print(Ttank[1:50], Eused[1:50], Eloss[1:50], control[1:50])
    
#    print(len(Ttank[0][:]))
    plt.figure(1)
    plt.clf()
    plt.plot(Ttank[0][0:20],'r*-',label = 'WH 1')
    plt.plot(Ttank[1][0:20],'bs-',label = 'WH 2')
    plt.plot(Ttank[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('Tank Temperature deg F')
    plt.xlabel('Hour')
    plt.legend()
    plt.ylim([0,170])
    
    plt.figure(2)
    plt.clf()
    plt.plot(SoC[0][0:20],'r*-',label = 'WH 1')
    plt.plot(SoC[1][0:20],'bs-',label = 'WH 2')
    plt.plot(SoC[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('SoC')
    plt.xlabel('Hour')
    plt.ylim([-0.5,1.2])
    plt.legend()
    plt.show()
    
    plt.figure(3)
    plt.clf()
    plt.plot(ServiceCallsAccepted[0][0:20],'r*-',label = 'WH 1')
    plt.plot(ServiceCallsAccepted[1][0:20],'bs-',label = 'WH 2')
    plt.plot(ServiceCallsAccepted[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('Service Calls Accepted')
    plt.xlabel('Hour')
    plt.legend()
    plt.show()

    plt.figure(4)
    plt.clf()
    plt.plot(ServiceProvided[0][0:20],'r*-',label = 'WH 1')
    plt.plot(ServiceProvided[1][0:20],'bs-',label = 'WH 2')
    plt.plot(ServiceProvided[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('Service Provided Per WH Per Timestep, W')
    plt.xlabel('Hour')
    plt.legend()
    plt.show()
    
    plt.figure(5)
    plt.clf()
#    plt.plot(TotalServiceProvided[0:20],'r*-',label='Provided by Fleet')
    plt.plot(TotalServiceProvidedPerTimeStep[0:20],'r*-',label='Provided by Fleet')
    plt.plot(fleet_load_request_total[0:20],'bs-', label ='Requested')
    plt.ylabel('Total Service During Timestep, W')
    plt.xlabel('Hour')
    plt.legend()
    plt.show()
    
    
#    x = np.linspace(0, 20, 1000)
#    y1 = np.sin(x)
#    y2 = np.cos(x)
#
#    plt.plot(x, y1, '-b', label='sine')
#    plt.plot(x, y2, '-r', label='cosine')
#    plt.legend(loc='upper left')
#    plt.ylim(-1.5, 2.0)
#    plt.show()
    
#    plt.figure(6)
#    plt.clf()
#    plt.hist(TotalServiceProvidedPerWH)
#    plt.xlabel('Service Level, Watts')
#    plt.show()
    
    plt.figure(7)
    plt.clf()
    plt.hist(TotalServiceCallsAcceptedPerWH)
    plt.xlabel('Total Service Calls Accepted per WH Annually')
    plt.show()
    
#    plt.figure(8)
#    plt.clf()
#    plt.plot(Ttank[0:100][0],'r')
#    plt.xlabel('Tank Temp for all WHs at one timesetp')
#    plt.xlim([0,100])
#    plt.show()
    
    plt.figure(9)
    plt.clf()
    plt.plot(AvailableCapacity[0][0:20],'r*-',label='0')
    plt.plot(AvailableCapacity[0][0:20],'bs-',label='1')
    plt.plot(AvailableCapacity[0][0:20],'k<-',label='2')
    plt.ylabel('Available Capacity, W')
    plt.xlabel('Hour')
    plt.legend()
    plt.show()

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