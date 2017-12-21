# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling fleet of water heaters
@author: cbooten
"""
import numpy as np
import os
#import csv
import matplotlib.pyplot as plt
#from annual_ewh_run import WaterHeater

from simple_wh_cwb_4 import ChuckWaterHeater
import random

def main():
    numWH = 20 #number of water heaters in fleet
    Steps = 20 #num steps in simulation
    lengthRegulation = 90# num of 4-second steps for regulation signal
    addshedTimestep = 60 #minutes, NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 1,2,3,4,5,6,10,12,15,20,30, 60
    MaxNumAnnualConditions = 20 #max # of annual conditions to calculate, if more WHs than this just reuse some of the conditions and water draw profiles
    TtankInitialMean = 125 #deg F
    TtankInitialStddev = 5 #deg F
    TsetInitialMean = 125 #deg F
    TsetInitialStddev = 5 #deg F
    minSOC = 0.2 # minimum SoC for aggregator to call for shed service
    maxSOC = 0.8 # minimum SoC for aggregator to call for add service
    minCapacityAdd = 350 #W-hr, minimum add capacity to be eligible for add service
    minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
    
    # for capacity, type and location need to specify discrete values and sample in such a way as to get overall distribution that I want 
    CapacityMasterList = [50,50,50,50,50,50,50,50,40,40,80] #70% 50 gal, 20% 40 gal, 10% 80 gal
    TypeMasterList = ['ER','ER','ER','ER','ER','ER','ER','ER','ER','HP'] #elec_resis 90% and HPWH 10%
    LocationMasterList =['living','living','living','living','unfinished basement'] #80% living, 20% unfinished basement for now
#    HotDrawMasterList = [0.2,0.15,0.1, 0.1, 0.05,0.05,0.02,0.01,0.01,0.01,0,0,0,0,0,0,0,0,0,0,0,0,0,0]#sample steply draw pattern. will randomly sample this 
    # 1x for each house and assume pattern is the same for that house for the entire year
    MaxServiceCallMasterList = [100,80,80, 200, 150, 110, 50, 75, 100]
    
    
        
        
    # define annual load service request 
    fleet_load_request = []
    fleet_load_request_total = []
#    numregs = []
#    
    ########################################################################
    #generate load request signal. capacity and regulation
    for step in range(Steps):
        magnitude_load_add_shed = (7e4 + 2e4*random.random())/(numWH/1) #def magnitude of request for load add/shed, assume only 50% of WH will be able to respond so request "too much" load effectively
        if step % 12 == 0 or step % 12 == 1 or step % 12 == 2:
            if step > 1:
                service = ['load shed',-magnitude_load_add_shed]
                s = -magnitude_load_add_shed * numWH / 1
            else:
                service = ['none',0]
                s=0
        elif step % 7 == 0 or step % 7 == 1:
            service = ['load add',magnitude_load_add_shed]
            s = magnitude_load_add_shed * numWH / 1
        
        elif step == 4: #minutely regulation service. NOTE: THIS IS THE STARTING STEP FOR REGULATION SERVICE
            service = ['regulation',0]
        else:
            service = ['none',0]
            s=0
        
        fleet_load_request_total.append(s)
        fleet_load_request.append(service)
        print(fleet_load_request[step][:])
    
#    #define regulation request separately since timescale is very different, have a 1hr schedule that will be repeated every time it is called
    fleet_regulation_request = []
    fleet_regulation_request_magnitude = []
    for second in range(lengthRegulation):
         #def magnitude of request for regulation
#        if second % 4 == 0: #send a new signal every 4 seconds
        magnitude_regulation = 5e2 + 2e3*random.uniform(-1,1)

        service =['regulation',magnitude_regulation]
            
        fleet_regulation_request.append(service)
        fleet_regulation_request_magnitude.append(magnitude_regulation)
    
#    print(fleet_regulation_request[0:50])
    #print(fleet_request)
#    print(len(fleet_regulation_request))
    
#    numsteps = Steps + numregs*3600 #adds steps for regulation into the time loops later
    
   ############################################################################# 
#    1) generate distribution of initial WH fleet states. this means Ttank, Tset, capacity, location (cond/uncond), type (elec resis or HPWH).
#    autogenerate water draw profile for the yr for each WH in fleet, this will be imported later, just get something reasonable here
    TtankInitial=np.random.normal(TtankInitialMean, TtankInitialStddev,numWH)
    TsetInitial=np.random.normal(TsetInitialMean, TsetInitialStddev,numWH)
    

    Capacity = [random.choice(CapacityMasterList) for n in range(numWH)]
    Type = [random.choice(TypeMasterList) for n in range(numWH)]
    Location = [random.choice(LocationMasterList) for n in range(numWH)]
#    Hot_draw = np.array([[random.choice(HotDrawMasterList) for h in range(24)] for i in range(numWH)])
    MaxServiceCalls = [random.choice(MaxServiceCallMasterList) for n in range(numWH)]
    climate_location = 'Denver' # only climate for now
    #for calculating annual conditions 
    
    
#    print(MaxServiceCalls)
    
#    (Tamb, RHamb, Tmains, hot_draw) = get_annual_conditions()
    
    
    #10 different units
    # bedrooms can be 1-5
    # gives 50 different draw profiles
    # can shift profiles by 0-365 days
    Tamb = []
    RHamb = []
    Tmains = []
#    numAggTimesteps = int(np.ceil(525600 / addshedTimestep))
    hot_draw =[]
    mixed_draw = []
    draw = []
    for a in range(numWH):             
        if a <= (MaxNumAnnualConditions-1): #if numWH > MaxNumAnnualConditions just start reusing older conditions to save computational time
            numbeds = random.randint(1, 5) 
            shift = random.randint(0, 364)
            unit = random.randint(0, 9)
            (tamb, rhamb, tmains, hotdraw, mixeddraw) = get_annual_conditions(climate_location,  Location[a], shift, numbeds, unit, addshedTimestep)
    #        print('max hot',max(hotdraw),'max mixed',max(mixeddraw))
    #        print('len tamb',len(tamb),len(tamb[0]),'max Tamb',max(tamb[0]))
    #        print('len rhamb',len(rhamb),len(rhamb[0]),'max RHamb',max(rhamb[0]))
    #        print('len tmains',len(tmains),len(tmains[0]),'max Tmains',max(tmains[0]))
    #        print('len hot',len(hotdraw),len(hotdraw[0]),'max hot_draw',max(hotdraw[0]))
    #        print('len mixeddraw',len(mixeddraw),len(mixeddraw[0]),'max mixed_draw',max(mixeddraw[0]))
    
            Tamb.append(tamb)
            RHamb.append(rhamb)
            Tmains.append(tmains)
            hot_draw.append(hotdraw)
            mixed_draw.append(mixeddraw)
            draw.append(hotdraw + 0.3 * mixeddraw)#0.5 is so you don't need to know the exact hot/cold mixture for mixed draws, just assume 1/2 is hot and 1/2 is cold
        else: #start re-using conditions
            Tamb.append(Tamb[a-MaxNumAnnualConditions][:])
            RHamb.append(RHamb[a-MaxNumAnnualConditions][:])
            Tmains.append(Tmains[a-MaxNumAnnualConditions][:])
            hot_draw.append(hot_draw[a-MaxNumAnnualConditions][:])
            mixed_draw.append(mixed_draw[a-MaxNumAnnualConditions][:])
            draw.append(hot_draw[a-MaxNumAnnualConditions][:] + 0.3 * mixed_draw[a-MaxNumAnnualConditions][:])
    
#    print('len draw',len(draw),len(draw[0]),'max draw',max(draw[0]))
#    print('len hotdraw',len(hot_draw),len(hot_draw[0]),'max hotdraw',max(hot_draw[0]))
#    print('hotdraw element',hot_draw[1][3])
#    print('len mixeddraw',len(mixed_draw),len(mixed_draw[0]),'max mixeddraw',max(mixed_draw[0]))
#    print('len Tamb',len(Tamb),len(Tamb[0]),'max Tamb',max(Tamb[0]))
#    print(Tamb[0][0:3],Tamb[1][0:3],Tamb[2][0:3],Tamb[3][0:3])
#    print(max(hot_draw[0]),max(hot_draw[1]),max(hot_draw[2]),max(hot_draw[3]))
#    print('len RHamb',len(RHamb),len(RHamb[0]),'max RHamb',max(RHamb[0]))
#    print('len Tmains',len(Tmains),len(Tmains[0]),'max Tmains',max(Tmains[0]))
#    print('len hot',len(hot_draw),len(hot_draw[0]),'max hot_draw',max(hot_draw[0]))
#    print('len mixed_draw',len(mixed_draw),len(mixed_draw[0]),'max mixed_draw',max(mixed_draw[0]))
#    plt.figure(6)
#    plt.clf()
#    plt.plot(Tamb[0][0:1000])  
#    plt.show()
#    
#    plt.figure(6)
#    plt.clf()
#    plt.plot(hot_draw[2][:])
#    plt.show()
    
#    print(Location[1:100])
    
    ###########################################################################    
    #3) at each timestep, rank fleet by:  available capacity and SoC and some algorithm for selecting units with minimum # of service calls). 
    
    
    
    #       goal is to optimize for calling WH with greatest availability but minimum number of calls. unsure exact form of algorithm.
    #5) add the load and regulation requests to get a single request
    #6) apply request down the ranked list until is satisfied
    
    Tset = [[0 for x in range(Steps)] for y in range(numWH)]
    Ttank = [[0 for x in range(Steps)] for y in range(numWH)]
    SoC = [[0 for x in range(Steps)] for y in range(numWH)]
    AvailableCapacityAdd = [[0 for x in range(Steps)] for y in range(numWH)]
    AvailableCapacityShed = [[0 for x in range(Steps)] for y in range(numWH)]
    ServiceCallsAccepted = [[0 for x in range(Steps)] for y in range(numWH)]
    ServiceProvided = [[0 for x in range(Steps)] for y in range(numWH)]
    IsAvailable = [[0 for x in range(Steps)] for y in range(numWH)]
    elementOn = [[0 for x in range(Steps)] for y in range(numWH)]
    TotalServiceProvidedPerWH = [0 for y in range(numWH)]
    TotalServiceProvidedPerTimeStep = [0 for y in range(Steps)]
    TotalServiceCallsAcceptedPerWH = [0 for y in range(numWH)]
#    TotalServiceProvided = [0 for y in range(numWH)]
    #items ending in "Reg" are only for timesteps where regulation is requested 
    TtankReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    SoCReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    IsAvailableReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    elementOnReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    AvailableCapacityAddReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)] 
    AvailableCapacityShedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)] 
    ServiceCallsAcceptedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)] 
    ServiceProvidedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    TotalServiceProvidedPerWHReg = [0 for y in range(numWH)]
    TotalServiceProvidedPerTimeStepReg = [0 for y in range(lengthRegulation)]
    TotalServiceCallsAcceptedPerWHReg = [0 for y in range(numWH)]
#    ttanktemp = [0 for y in range(numWH)]
#    TtankLast = [0 for y in range(numWH)]

    whs = [ChuckWaterHeater(Tamb[0], RHamb[0], Tmains[0], 0, fleet_load_request[0], Capacity[number], Type[number], Location[number], 0, MaxServiceCalls[number]) for number in range(numWH)]
               
    for step in range(Steps):    
        number = 0
        servsum = 0
#        capsum = 0
        request = 0
        NumDevicesToCall = 0
        laststep = step - 1
#        stepOfDay = step % 24
        if fleet_load_request[step][0] != 'regulation': #not providing regulation
#            print(fleet_load_request[step])
            #decision making about which WH to call on for service, check if available at last step, if so then 
            # check for SoC > X%, whatever number that is, divide the total needed and ask for that for each
            
            if step > 0:
                for n in range(numWH):
                    if fleet_load_request[step][0] == 'load add' and IsAvailable[n][laststep] > 0 and SoC[n][laststep] < maxSOC and AvailableCapacityAdd[n][laststep] > minCapacityAdd:
                        NumDevicesToCall += 1
    #                    print('ask add')
                    elif fleet_load_request[step][0] == 'load shed' and IsAvailable[n][laststep] > 0 and SoC[n][laststep] > minSOC and AvailableCapacityShed[n][laststep] > minCapacityShed:
                        NumDevicesToCall += 1
    #                    print('ask shed')
          
                
    #            print('num devices',NumDevicesToCall,'is avail',IsAvailable[n][laststep],'soc',SoC[n][laststep])
                if fleet_load_request[step][1] < 0 and NumDevicesToCall > 0: #if shed is called for and there are some devices that can respond
                    newrequest = fleet_load_request_total[step] / (NumDevicesToCall/9.5*np.exp(-numWH/20)+1) #9.5*exp(-numWH/20)+1 ad hoc curve fit based on trying numWH = 20,30,10,200 and doing hand curve fit. 
                elif fleet_load_request[step][1] > 0 and NumDevicesToCall > 0: # easier to do load add, but some "available" devices still won't be able to respond so ask for extra 
    #                newrequest = fleet_load_request_total[step] / (NumDevicesToCall/(9.5*np.exp(-numWH/20)+1)) #9.5*exp(-numWH/20)+1 ad hoc curve fit based on trying numWH = 20,30,10,200 and doing hand curve fit. 
                    newrequest = fleet_load_request_total[step] / (NumDevicesToCall/2)
                else:
                    newrequest = fleet_load_request_total[step]
                    
                fleet_load_request[step] = [fleet_load_request[step][0],newrequest]
#                print('request',fleet_load_request[step])
        
        
        
            for wh in whs: #numWH
                if step == 0:
                    ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailable, elementon = wh.execute(TtankInitial[number], TsetInitial[number], Tamb[number][0], RHamb[number][0], Tmains[number][0], draw[number][0], fleet_load_request[0], ServiceCallsAccepted[number][0], elementOn[number][0], addshedTimestep)
    #                print('WH num',number,'tank',ttank,'soc',soC,'calls accepted', serviceCallsAccepted,'available?',isAvailable,'request',fleet_load_request[0])
#                    TtankLast= ttank[0] 
#                    print('tankinitial',TtankInitial[number])
#                    print('tanklast',ttank)
#                    print('step',step,'number',number)
                else:
                    
                    TsetLast = Tset[number][laststep]
                    TtankLast = Ttank[number][laststep]
#                    print('tanklast',TtankLast)
#                    print('setlast',TsetLast)
#                    print('num',number,'lasthr',laststep)
#                    print('numWH',len(Ttank),'steps',len(Ttank[0]))
#                    print('ttank',Ttank[number][laststep])
                    
                    ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailable, elementon = wh.execute(TtankLast, TsetLast, Tamb[number][step], RHamb[number][step], Tmains[number][step], draw[number][step], fleet_load_request[step], ServiceCallsAccepted[number][laststep], elementOn[number][laststep], addshedTimestep)
    #                print('WH num',number,'tank',ttank,'soc',soC,'calls accepted', serviceCallsAccepted,'available?',isAvailable,'request',fleet_load_request[step])
    #                print('request',fleet_load_request[step],'service',eservice)
                Tset[number][step] = tset
                
    #            print('provided',eservice)
                Ttank[number][step] = ttank
#                print('ttank',ttank)
#                ttanktemp[number] = ttank
#                TtankLast = ttank
                SoC[number][step] = soC
                IsAvailable[number][step] = isAvailable
                elementOn[number][step] = elementon
                AvailableCapacityAdd[number][step] = availableCapacityAdd
                AvailableCapacityShed[number][step] = availableCapacityShed
    #            capsum += availableCapacity
                ServiceCallsAccepted[number][step] = serviceCallsAccepted
                ServiceProvided[number][step] = eservice
                servsum += eservice
                
                TotalServiceProvidedPerWH[number] = TotalServiceProvidedPerWH[number] + ServiceProvided[number][step]
    #            print('number',number,'hr',step,TotalServiceProvidedPerWH)
    #            print('provided per hr',servsum)
                request += fleet_load_request[step][1] 
                number += 1
#            print('step',step,'provided per hr',servsum)    
            TotalServiceProvidedPerTimeStep[step] += servsum #ServiceProvided[number][step]
#            print(TsetLast)
        
        #########################################################################
        if  fleet_load_request[step][0] == 'regulation':
            
#            if step == 4:
#                plt.figure(20)
#                plt.clf()
#                plt.hist(ttanktemp)
#                plt.xlabel('Ttank distribution going into regulation')
#                plt.show()
                
                
            for reg_step in range(lengthRegulation):
                NumDevicesToCall = 0
                servsumReg = 0
                #assume this won't be called unless step > 0
                number = 0 #need to reset since i'll be looping through a different timestep
                if reg_step == 0:
                    lastStep = laststep
                    #figure how many devices to call for the regulation service
                    for n in range(numWH):
                        if IsAvailable[n][lastStep] > 0 and SoC[n][lastStep] > minSOC and SoC[n][lastStep] < maxSOC: #don't specify min capacity to be available for regulation
                            NumDevicesToCall += 1
                else:
                    lastStep = reg_step -1
                    #figure how many devices to call for the regulation service
                    n = 0
                    for n in range(numWH):
                        
                        if IsAvailableReg[n][lastStep] > 0 and SoCReg[n][lastStep] > minSOC and SoCReg[n][lastStep] < maxSOC: #don't specify min capacity to be available for regulation
                            NumDevicesToCall += 1
                    
                
                
                #figure out how much to ask of each device
                if fleet_regulation_request[reg_step][1] != 0 and NumDevicesToCall > 0: 
                    newrequest = fleet_regulation_request[reg_step][1] / NumDevicesToCall #since timestep is small, assume that all devices available last step will be available for this step
                else:
                    newrequest = fleet_regulation_request[reg_step][1]
                        
                fleet_regulation_request[reg_step] = [fleet_regulation_request[reg_step][0],newrequest]
#                print(fleet_regulation_request[step])
                
                for wh in whs: #numWH, assume won't be called unless step > 0        
#                    TsetLast = Tset[number][llastStepaststep]# dont' change during regulation
                    if reg_step == 0:
                        TtankLast = Ttank[number][lastStep]
                    else:
                        TtankLast = TtankReg[number][lastStep]
#                    print('TtankLast',TtankLast, 'num',number,'step',step)
#                    print('hotdraw',hot_draw[number][stepOfDay])
#                   
#                    print('Tamb',Tamb[number][step],'num',number,'hr',step,'step',step)
                    ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailable, elementon = wh.execute(TtankLast, TsetLast, Tamb[number][step], RHamb[number][step], Tmains[number][step], draw[number][step], fleet_regulation_request[reg_step], ServiceCallsAcceptedReg[number][lastStep], elementOnReg[number][lastStep], addshedTimestep)
    #                print('WH num',number,'tank',ttank,'soc',soC,'calls accepted', serviceCallsAccepted,'available?',isAvailable,'request',fleet_load_request[step])
    #                print('request',fleet_load_request[step],'service',eservice)
#                    Tset[number][step] = tset
#                    print('provided',eservice)
                    TtankReg[number][reg_step] = ttank
                    SoCReg[number][reg_step] = soC
#                    print('soc',soC)
                    IsAvailableReg[number][reg_step] = isAvailable
                    elementOnReg[number][reg_step] = elementon
                    AvailableCapacityAddReg[number][reg_step] = availableCapacityAdd
                    AvailableCapacityShedReg[number][reg_step] = availableCapacityShed
                    ServiceCallsAcceptedReg[number][reg_step] = serviceCallsAccepted
                    ServiceProvidedReg[number][reg_step] = eservice
                    servsumReg += eservice
                    TotalServiceProvidedPerWHReg[number] = TotalServiceProvidedPerWHReg[number] + ServiceProvidedReg[number][reg_step]
#                    print(ServiceProvidedReg[number][step])
#                    print(TotalServiceProvidedPerWHReg[number])
#                    print(eservice)
                    if reg_step == lengthRegulation-1: # save variables to change back to steply
#                        print('step',step)
                        Ttank[number][step] = ttank
                        SoC[number][step] = soC
                        IsAvailable[number][step] = isAvailable
                        elementOn[number][step] = elementon
                        AvailableCapacityAdd[number][step] = availableCapacityAdd
                        AvailableCapacityShed[number][step] = availableCapacityShed
                        ServiceCallsAccepted[number][step] = ServiceCallsAccepted[number][laststep] # don't count regulation as service calls, if want to add this then substitute 'serviceCallsAccepted' for what is here
                        ServiceProvided[number][step] = eservice
                        servsum += eservice
                        TotalServiceProvidedPerWH[number] = TotalServiceProvidedPerWH[number] + ServiceProvided[number][step]
        #            print('number',number,'hr',step,TotalServiceProvidedPerWH)
#                        print('number',number, 'provided per hr',servsum) 
                    number += 1
                TotalServiceProvidedPerTimeStepReg[reg_step] += servsumReg
#                print(TtankReg[number][step])
#                print('step',step)    
                TotalServiceProvidedPerTimeStep[step] += servsum #update for the next step when no longer in regulation mode
                
                for n in range(number):
                    TotalServiceCallsAcceptedPerWHReg[n] = ServiceCallsAcceptedReg[n][reg_step]
            
            
#    print('ttank',Ttank[0:20][1])
#    print(number)
#        print('hr',step,'provided',TotalServiceProvidedPerTimeStep[step],'request',request,'available',capsum)
#            print(Ttank[number][step])
            
#    print(ServiceCallsAccepted)
#    print(TotalServiceProvidedPerTimeStep)
    
    for n in range(number):
        TotalServiceCallsAcceptedPerWH[n] = ServiceCallsAccepted[n][step]
#        TotalServiceProvided[n] = ServiceProvided[n][step]
#        print(ServiceProvided[n][step])
        #analysis   
#        for wh in whs:
#            wh_thistory[wh,:] = np.array(wh.temp_history)  
            
    
#    print(len(Ttank[0][:]))
    plt.figure(1)
    plt.clf()
    plt.plot(draw[0][0:20],'r*-',label = 'WH 1')
    plt.plot(draw[1][0:20],'bs-',label = 'WH 2')
    plt.plot(draw[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('Water Draw [gal]')
    plt.xlabel('step')
    plt.legend()
    plt.ylim([0,30])
    
    plt.figure(2)
    plt.clf()
    plt.plot(Ttank[0][0:50],'r*-',label = 'WH 1')
    plt.plot(Ttank[1][0:50],'bs-',label = 'WH 2')
    plt.plot(Ttank[2][0:50],'k<-',label = 'WH 3')
#    plt.plot(hot_draw[0][0:50],'r*--',label = 'WH 1')
#    plt.plot(hot_draw[1][0:50],'bs--',label = 'WH 2')
#    plt.plot(hot_draw[2][0:50],'k<--',label = 'WH 3')
    plt.ylabel('Ttank')
    plt.xlabel('step')
    plt.ylim([0,170])
    plt.legend()
    plt.show()
    
    plt.figure(3)
    plt.clf()
    plt.plot(ServiceCallsAccepted[0][0:20],'r*-',label = 'WH 1')
    plt.plot(ServiceCallsAccepted[1][0:20],'bs-',label = 'WH 2')
    plt.plot(ServiceCallsAccepted[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('Service Calls Accepted - Not Inc. Regulation')
    plt.xlabel('step')
    plt.legend()
    plt.show()

    plt.figure(4)
    plt.clf()
    plt.plot(ServiceProvided[0][0:50],'r*-',label = 'WH 1')
    plt.plot(ServiceProvided[1][0:50],'bs-',label = 'WH 2')
    plt.plot(ServiceProvided[2][0:50],'k<-',label = 'WH 3')
    plt.ylabel('Service Provided Per WH Per Timestep, W')
    plt.xlabel('step')
    plt.legend()
    plt.show()
    
    plt.figure(5)
    plt.clf()
#    plt.plot(TotalServiceProvided[0:20],'r*-',label='Provided by Fleet')
    plt.plot(TotalServiceProvidedPerTimeStep[0:20],'r*-',label='Provided by Fleet')
    plt.plot(fleet_load_request_total[0:20],'bs-', label ='Requested')
    plt.ylabel('Total Service During Timestep, W')
    plt.xlabel('step')
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
    plt.plot(AvailableCapacityAdd[0][0:20],'r*-',label='0')
    plt.plot(AvailableCapacityAdd[1][0:20],'bs-',label='1')
    plt.plot(AvailableCapacityAdd[2][0:20],'k<-',label='2')
    plt.ylabel('Available Capacity for Load Add, W-hr')
    plt.xlabel('step')
    plt.legend()
    plt.show()
    
    plt.figure(10)
    plt.clf()
    plt.plot(AvailableCapacityShed[0][0:20],'r*-',label='0')
    plt.plot(AvailableCapacityShed[1][0:20],'bs-',label='1')
    plt.plot(AvailableCapacityShed[2][0:20],'k<-',label='2')
    plt.ylabel('Available Capacity for Load Shed, W-hr')
    plt.xlabel('step')
    plt.legend()
    plt.show()
    
    
    ##########################################################################
    #plotting regulation responses
    plt.figure(11)
    plt.clf()
    plt.plot(TtankReg[0][0:20],'r*-',label = 'WH 1')
    plt.plot(TtankReg[1][0:20],'bs-',label = 'WH 2')
    plt.plot(TtankReg[2][0:20],'k<-',label = 'WH 3')
    plt.ylabel('Tank Temperature deg F')
    plt.xlabel('Regulation Timestep')
    plt.legend()
    plt.ylim([0,170])
    
    plt.figure(12)
    plt.clf()
    plt.plot(SoCReg[0][0:50],'r*-',label = 'WH 1')
    plt.plot(SoCReg[1][0:50],'bs-',label = 'WH 2')
    plt.plot(SoCReg[2][0:50],'k<-',label = 'WH 3')
    plt.ylabel('SoC')
    plt.xlabel('Regulation Timestep')
    plt.ylim([-0.5,1.2])
    plt.legend()
    plt.show()
    
    plt.figure(13)
    plt.clf()
    plt.plot(ServiceCallsAcceptedReg[0][0:50],'r*-',label = 'WH 1')
    plt.plot(ServiceCallsAcceptedReg[1][0:50],'bs-',label = 'WH 2')
    plt.plot(ServiceCallsAcceptedReg[2][0:50],'k<-',label = 'WH 3')
    plt.ylabel('Service Calls Accepted')
    plt.xlabel('Regulation Timestep')
    plt.legend()
    plt.show()

    plt.figure(14)
    plt.clf()
    plt.plot(ServiceProvidedReg[0][0:50],'r*-',label = 'WH 1')
    plt.plot(ServiceProvidedReg[1][0:50],'bs-',label = 'WH 2')
    plt.plot(ServiceProvidedReg[2][0:50],'k<-',label = 'WH 3')
    plt.plot(ServiceProvidedReg[3][0:50],'go-',label = 'WH 4')
    plt.ylabel('Service Provided Per WH Per Timestep, W')
    plt.xlabel('Regulation Timestep')
    plt.legend()
    plt.show()
    
    plt.figure(15)
    plt.clf()
#    plt.plot(TotalServiceProvided[0:20],'r*-',label='Provided by Fleet')
    plt.plot(TotalServiceProvidedPerTimeStepReg[0:50],'r*-',label='Provided by Fleet')
    plt.plot(fleet_regulation_request_magnitude[0:50],'bs-', label ='Requested')
    plt.ylabel('Total Service During Timestep, W')
    plt.xlabel('Regulation Timestep')
    plt.legend()
    plt.show()
    
    plt.figure(16)
    plt.clf()
    plt.hist(TotalServiceCallsAcceptedPerWHReg)
    plt.xlabel('Total Service Calls Accepted per WH Annually')
    plt.show()
    
#    plt.figure(8)
#    plt.clf()
#    plt.plot(Ttank[0:100][0],'r')
#    plt.xlabel('Tank Temp for all WHs at one timesetp')
#    plt.xlim([0,100])
#    plt.show()
    
    plt.figure(17)
    plt.clf()
    plt.plot(AvailableCapacityAddReg[0][0:50],'r*-',label='0')
    plt.plot(AvailableCapacityAddReg[1][0:50],'bs-',label='1')
    plt.plot(AvailableCapacityAddReg[2][0:50],'k<-',label='2')
    plt.ylabel('Available Capacity for Load Add, W-hr')
    plt.xlabel('Regulation Timestep')
    plt.legend()
    plt.show()
    
    plt.figure(18)
    plt.clf()
    plt.plot(AvailableCapacityShedReg[0][0:50],'r*-',label='0')
    plt.plot(AvailableCapacityShedReg[1][0:50],'bs-',label='1')
    plt.plot(AvailableCapacityShedReg[2][0:50],'k<-',label='2')
    plt.ylabel('Available Capacity for Load Shed, W-hr')
    plt.xlabel('Regulation Timestep')
    plt.legend()
    plt.show()


##############################################################################
#def get_annual_conditions():
#        Tamb = []
#        RHamb = []
#        Tmains = []
#        hot_draw = []
#        
#        for step in range(8760):
#            if step >  4000:   
#                Tamb.append(65) # deg F
#                RHamb.append(30) #%
#                Tmains.append(55) # deg F
#            else:
#                Tamb.append(45) # deg F
#                RHamb.append(40) #%
#                Tmains.append(40) # deg F
#            if step % 5 == 0: #if step is divisible by 5
#                hot_draw.append(0.5) #gpm
#            else:
#                hot_draw.append(0)
#   
#        return Tamb, RHamb, Tmains, hot_draw
    
    
###############################################################################    
# from Jeff Maguire annual_ewh_run.py on December, 11, 2017
# modifications by CWB, eliminate 'self', eliminated 'initial_time' 
    
def get_annual_conditions(climate_location, installation_location, days_shift,n_br,unit,timestep_min):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        #TODO: RH is currently unused, will need to import some psych calculations to get a WB
        #TODO: Use a .epw weather file? We'll eventually need atmospheric pressure (for psych calcs), could also estimate unconditioned space temp/rh based on ambient or calc mains directly based on weather file info
        Tamb = []
        RHamb = []
        Tmains = []
        if climate_location != 'Denver':
            raise NameError("Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
        if installation_location == 'living':
            amb_temp_column = 1
            amb_rh_column = 2
        elif installation_location == 'unfinished basement':
            amb_temp_column = 3
            amb_rh_column = 4
        elif installation_location == 'garage':
            amb_temp_column = 5
            amb_rh_column = 6
        elif installation_location == 'unifinished attic':
            amb_temp_column = 7
            amb_rh_column = 8
        else:
            raise NameError("Error! Only allowed installation locations are living, unfinished basement, garage, unfinished attic. Change the installation location to a valid location")
        mains_temp_column = 9
        
        linenum = 0
        
        ambient_cond_file = open((os.path.join(os.path.dirname(__file__),'data_files','denver_conditions.csv')),'r') #steply ambient air temperature and RH
        for line in ambient_cond_file:
            if linenum > 0: #skip header
                items = line.strip().split(',')
                for b in range(int(60/timestep_min)): # repeat depending on how many timesteps per step there are.
                    Tamb.append([float(items[amb_temp_column])])
                    RHamb.append([float(items[amb_rh_column])])
                    Tmains.append([float(items[mains_temp_column])])
            linenum += 1
        ambient_cond_file.close()
        
        #Read in max and average values for the draw profiles
        #TODO: we only need to do this once when we start running a large number of water heaters, we might want to break this out into somewhere else where we only read this file once while initializing
        linenum = 0
        n_beds = 0
        n_unit = 0
        
        #Total gal/day draw numbers based on BA HSP
        sh_hsp_tot = 14.0 + 4.67 * float(n_br)
        s_hsp_tot = 12.5 + 4.16 * float(n_br)
        cw_hsp_tot = 2.35 + 0.78 * float(n_br)
        dw_hsp_tot = 2.26 + 0.75 * float(n_br)
        b_hsp_tot = 3.50 + 1.17 * float(n_br)
        
        sh_max = np.zeros((5,10))
        s_max = np.zeros((5,10))
        b_max = np.zeros((5,10))
        cw_max = np.zeros((5,10))
        dw_max = np.zeros((5,10))
        sh_sum = np.zeros((5,10))
        s_sum = np.zeros((5,10))
        b_sum = np.zeros((5,10))
        cw_sum = np.zeros((5,10))
        dw_sum = np.zeros((5,10))
        
        sum_max_flows_file = open((os.path.join(os.path.dirname(__file__),'data_files', 'DrawProfiles','MinuteDrawProfilesMaxFlows.csv')),'r') #sum and max flows for all units and # of bedrooms
        for line in sum_max_flows_file:
            if linenum > 0:
                items = line.strip().split(',')
                n_beds = int(items[0]) - 1
                n_unit = int(items[1]) - 1
                 #column is unit number, row is # of bedrooms. Taken directly from BEopt
                sh_max[n_beds, n_unit] = float(items[2])
                s_max[n_beds, n_unit] = float(items[3])
                b_max[n_beds, n_unit] = float(items[4])
                cw_max[n_beds, n_unit] = float(items[5])
                dw_max[n_beds, n_unit] = float(items[6])
                sh_sum[n_beds, n_unit] = float(items[7])
                s_sum[n_beds, n_unit] = float(items[8])
                b_sum[n_beds, n_unit] = float(items[9])
                cw_sum[n_beds, n_unit] = float(items[10])
                dw_sum[n_beds, n_unit] = float(items[11])
            linenum += 1
        sum_max_flows_file.close()
        
        linenum = 0
        #Read in individual draw profiles
        steps_per_year = int(np.ceil(60 * 24 * 365 / timestep_min))
        hot_draw = np.zeros((steps_per_year,1))
        mixed_draw = np.zeros((steps_per_year,1))
        #take into account days shifted
        draw_idx = 60 * 24 * days_shift
        draw_profile_file = open((os.path.join(os.path.dirname(__file__),'data_files','DrawProfiles','DHWDrawSchedule_{}bed_unit{}_1min_fraction.csv'.format(n_br,unit))),'r') #minutely draw profile (shower, sink, CW, DW, bath)
        agghotflow = 0.0
        aggmixflow = 0.0
        for line in draw_profile_file:
            nbr = n_br - 1 #go back to starting index at zero for python internal calcs
            if linenum > 0:
                items = line.strip().split(',')
                hot_flow = 0.0
                mixed_flow = 0.0
                
                if items[0] != '':
                    sh_draw = float(items[0]) * sh_max[nbr,unit] * (sh_hsp_tot / sh_sum[nbr,unit])
                    mixed_flow += sh_draw
                if items[1] != '':
                    s_draw = float(items[1]) * s_max[nbr,unit] * (s_hsp_tot / s_sum[nbr,unit])
                    mixed_flow += s_draw
                if items[2] != '':
                    cw_draw = float(items[2]) * cw_max[nbr,unit] * (cw_hsp_tot / cw_sum[nbr,unit])
                    hot_flow += cw_draw
                if items[3] != '':
                    dw_draw = float(items[3]) * dw_max[nbr,unit] * (dw_hsp_tot / dw_sum[nbr,unit])
                    hot_flow += dw_draw
                if items[4] != '':
                    b_draw = float(items[4]) * b_max[nbr,unit] * (b_hsp_tot / b_sum[nbr,unit])
                    mixed_flow += b_draw
#                hot_draw[draw_idx] = hot_flow
#                mixed_draw[draw_idx] = mixed_flow
#                print('maxhot',max(hot_draw))
                agghotflow += hot_flow
                aggmixflow += mixed_flow
#                    print('hot',hot_flow,'mixed',mixed_flow)
                if linenum % timestep_min == 0: #aggregate
#                    print('hot',agghotflow,'mixed',mixed_flow)
                    hot_draw[draw_idx] = agghotflow
                    mixed_draw[draw_idx] = aggmixflow
                    agghotflow = 0
                    aggmixflow = 0
                    draw_idx += 1
            linenum += 1
            if draw_idx >= steps_per_year:
                draw_idx = 0
        draw_profile_file.close()
#        time_draw_profile_completed = time.time()
#        time_load_draw = time_draw_profile_completed - initial_time
#        print("Loaded draw profile after {} seconds".format(time_load_draw))
        
#        print('max hot',max(hot_draw),'max mixed',max(mixed_draw))
#        print('len Tamb',len(Tamb),'len RHamb',len(RHamb),'len Tmains',len(Tmains),'len hot',len(hot_draw),'len mixed',len(mixed_draw))
        return Tamb, RHamb, Tmains, hot_draw, mixed_draw




if __name__ == '__main__':
    main()