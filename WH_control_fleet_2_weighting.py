# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 10:28:48 2017
creating and controlling a fleet of water heaters
@author: chuck booten, jeff maguire, xin jin
"""
# depending on the IDE used these libraries might need to be imported manually
import numpy as np
import os
import matplotlib.pyplot as plt
import random

# this is the actual water heater model
from draft_wh_1_adv_availability_forecasting import WaterHeater


def main():
    numWH = 300 #number of water heaters to be simulated to represent the entire fleet
    Fleet_size_represented = max(numWH, 1e5)#size of the fleet that is represented by numWH
    Steps = 10 #num steps in simulation
    lengthRegulation = 90# num of 4-second steps for regulation signal
    addshedTimestep = 10 #minutes, NOTE, MUST BE A DIVISOR OF 60. Acceptable numbers are: 1,2,3,4,5,6,10,12,15,20,30, 60
    MaxNumAnnualConditions = 20 #max # of annual conditions to calculate, if more WHs than this just reuse some of the conditions and water draw profiles
    TtankInitialMean = 125 #deg F
    TtankInitialStddev = 5 #deg F
    TsetInitialMean = 125 #deg F
    TsetInitialStddev = 5 #deg F
    minSOC = 0.2 # minimum SoC for aggregator to call for shed service
    maxSOC = 0.8 # minimum SoC for aggregator to call for add service
    minCapacityAdd = 350 #W-hr, minimum add capacity to be eligible for add service
    minCapacityShed = 150 #W-hr, minimum shed capacity to be eligible for shed service
    
    # for capacity, type, location and max. number of service calls need to specify discrete values and randomly sample to get a desired distribution 
    CapacityMasterList = [50,50,50,50,50,50,50,50,40,40,80] #70% 50 gal, 20% 40 gal, 10% 80 gal
    TypeMasterList = ['ER','ER','ER','ER','ER','ER','ER','ER','ER','HP'] #elec_resis 90% and HPWH 10%
    LocationMasterList =['living','living','living','living','unfinished basement'] #80% living, 20% unfinished basement for now
    MaxServiceCallMasterList = [100,80,80, 200, 150, 110, 50, 75, 100] # this is the max number of annual service calls for load add/shed.            

    ########################################################################
    #generate load request signal and regulation
#    NOTE: code is set up to deal with capacity separately from regulation, the only interface is in the capacity signal there is a single timestep
#    where regulation is called, the entire code switches into regulation mode for that single timestep (which is much longer than a regulation timestep)
#    when the calculations are complete, it returns conditions to be used for subsequent capacity timesteps
    fleet_load_request = []
    fleet_load_request_total = []
    
    for step in range(Steps):
        capacity_needed = 1e6 + 2e5*random.random()#Watts needed, >0 is capacity add, <0 is capacity shed
#        Fleet_size_represented = capacity_needed/4500 # approximately how many WH would be needed to be able to provide this capacity
        magnitude_load_add_shed = capacity_needed/Fleet_size_represented #def magnitude of request for load add/shed
        if step % 12 == 0 or step % 12 == 1 or step % 12 == 2: # this is my aribtrary but not random way of creating load add/shed events. should be replaced with a more realistic signal at some point
            if step > 1:
                service = ['load shed',-magnitude_load_add_shed]
                s = -magnitude_load_add_shed * numWH / 1
            else:
                service = ['none',0]
                s=0
        elif step % 7 == 0 or step % 7 == 1:
            service = ['load add',magnitude_load_add_shed]
            s = magnitude_load_add_shed * numWH / 1
        
        elif step == 4000: #minutely regulation service. NOTE: THIS IS THE STARTING STEP FOR REGULATION SERVICE
            service = ['regulation',0]
        else:
            service = ['none',0]
            s=0
        
#        NOTE: the load request signal has two components, the string component (load add, shed or regulation) and the numerical component, not sure if this will ultimately be necessary
        fleet_load_request_total.append(s)
        fleet_load_request.append(service)
    
    
    
#   define regulation request separately since timescale is very different, have a 1hr schedule that will be repeated every time it is called
    fleet_regulation_request = []
    fleet_regulation_request_magnitude = []
    for second in range(lengthRegulation):
         #def magnitude of request for regulation
        magnitude_regulation = 5e2 + 2e3*random.uniform(-1,1)

        service =['regulation',magnitude_regulation]
            
        fleet_regulation_request.append(service)
        fleet_regulation_request_magnitude.append(magnitude_regulation)
    
    
   ############################################################################# 
#    generate distribution of initial WH fleet states. this means Ttank, Tset, capacity, location (cond/uncond), type (elec resis or HPWH).
#    autogenerate water draw profile for the yr for each WH in fleet, this will be imported later, just get something reasonable here
    TtankInitial=np.random.normal(TtankInitialMean, TtankInitialStddev,numWH)
    TsetInitial=np.random.normal(TsetInitialMean, TsetInitialStddev,numWH)
    Capacity = [random.choice(CapacityMasterList) for n in range(numWH)]
    Capacity_fleet_ave = sum(Capacity)/numWH
    Type = [random.choice(TypeMasterList) for n in range(numWH)]
    Location = [random.choice(LocationMasterList) for n in range(numWH)]
    MaxServiceCalls = [random.choice(MaxServiceCallMasterList) for n in range(numWH)]
    
    
    #for calculating annual conditions
    climate_location = 'Denver' # only allowable climate for now since the pre-run water draw profile generator has only been run for this climate
#    10 different profiles for each number of bedrooms
#    bedrooms can be 1-5
#    gives 50 different draw profiles
#    can shift profiles by 0-364 days
#    gives 365*50 = 18250 different water draw profiles for each climate
    Tamb = []
    RHamb = []
    Tmains = []
    hot_draw =[]
    mixed_draw = []
    draw = []
    for a in range(numWH):             
        if a <= (MaxNumAnnualConditions-1): #if numWH > MaxNumAnnualConditions just start reusing older conditions to save computational time
            numbeds = random.randint(1, 5) 
            shift = random.randint(0, 364)
            unit = random.randint(0, 9)
            (tamb, rhamb, tmains, hotdraw, mixeddraw) = get_annual_conditions(climate_location,  Location[a], shift, numbeds, unit, addshedTimestep)
    
            Tamb.append(tamb)
            RHamb.append(rhamb)
            Tmains.append(tmains)
            hot_draw.append(hotdraw)
            mixed_draw.append(mixeddraw)
            draw.append(hotdraw + 0.3 * mixeddraw)#0.3 is so you don't need to know the exact hot/cold mixture for mixed draws, just assume 1/2 is hot and 1/2 is cold

        else: #start re-using conditions
            Tamb.append(Tamb[a-MaxNumAnnualConditions][:])
            RHamb.append(RHamb[a-MaxNumAnnualConditions][:])
            Tmains.append(Tmains[a-MaxNumAnnualConditions][:])
            hot_draw.append(hot_draw[a-MaxNumAnnualConditions][:])
            mixed_draw.append(mixed_draw[a-MaxNumAnnualConditions][:])
            draw.append(hot_draw[a-MaxNumAnnualConditions][:] + 0.3 * mixed_draw[a-MaxNumAnnualConditions][:])


    draw_fleet = sum(draw)# this sums all rows, where each row is a WH, so gives the fleet sum of hot draw at each step
    draw_fleet_ave = draw_fleet/numWH  # this averages all rows, where each row is a WH, so gives the fleet average of hot draw at each step

   
#    plt.figure(19)
#    plt.clf()
##    plt.plot(hot_draw_fleet[0:200], 'k<-', label = 'hot')
#    plt.plot(draw_fleet_ave[0:200], 'ro-',label = 'ave draw')
#    plt.ylabel('Hot draw fleet [gal/step]')
#    plt.legend()
#    plt.xlabel('step')

    ###########################################################################  
    
    ##################################     
#    Initializing lists to be saved to track indivisual water heater performance over each timestep
    Tset = [[0 for x in range(Steps)] for y in range(numWH)]
    Ttank = [[0 for x in range(Steps)] for y in range(numWH)]
    dTtank_set = [[0 for x in range(Steps)] for y in range(numWH)]
    SoC = [[0 for x in range(Steps)] for y in range(numWH)]
    AvailableCapacityAdd = [[0 for x in range(Steps)] for y in range(numWH)]
    AvailableCapacityShed = [[0 for x in range(Steps)] for y in range(numWH)]
    ServiceCallsAccepted = [[0 for x in range(Steps)] for y in range(numWH)]
    ServiceProvided = [[0 for x in range(Steps)] for y in range(numWH)]
    IsAvailableAdd = [[0 for x in range(Steps)] for y in range(numWH)]
    IsAvailableShed = [[0 for x in range(Steps)] for y in range(numWH)]
    elementOn = [[0 for x in range(Steps)] for y in range(numWH)]
    TotalServiceProvidedPerWH = [0 for y in range(numWH)]
    TotalServiceProvidedPerTimeStep = [0 for y in range(Steps)]
    TotalServiceCallsAcceptedPerWH = [0 for y in range(numWH)]

    #items ending in "Reg" are only for timesteps where regulation is requested 
    TtankReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    SoCReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    IsAvailableAddReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    IsAvailableShedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    elementOnReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    AvailableCapacityAddReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)] 
    AvailableCapacityShedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)] 
    ServiceCallsAcceptedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)] 
    ServiceProvidedReg = [[0 for x in range(lengthRegulation)] for y in range(numWH)]
    TotalServiceProvidedPerWHReg = [0 for y in range(numWH)]
    TotalServiceProvidedPerTimeStepReg = [0 for y in range(lengthRegulation)]
    TotalServiceCallsAcceptedPerWHReg = [0 for y in range(numWH)]
    ##################################
    

#    Initializing the water heater models
    whs = [WaterHeater(Tamb[0], RHamb[0], Tmains[0], 0, fleet_load_request[0], Capacity[number], Type[number], Location[number], 0, MaxServiceCalls[number]) for number in range(numWH)]
               
    for step in range(Steps):    
        number = 0
        servsum = 0
        request = 0
        NumDevicesToCall = 0
        laststep = step - 1

        if fleet_load_request[step][0] != 'regulation': #NOT providing regulation

#            decision making about which WH to call on for service, check if available at last step, if so then 
#            check for SoC > minSOC and Soc < maxSOC, whatever number that is, divide the total needed and ask for that for each
#            decided to add max and min SoC limits just in case, they might not matter but wanted limits other than just whether a device was available 
#            at the last timestep
            if step > 0:
                for n in range(numWH):
                    if fleet_load_request[step][0] == 'load add' and IsAvailableAdd[n][laststep] > 0 and SoC[n][laststep] < maxSOC and AvailableCapacityAdd[n][laststep] > minCapacityAdd:
                        NumDevicesToCall += 1
                    elif fleet_load_request[step][0] == 'load shed' and IsAvailableShed[n][laststep] > 0 and SoC[n][laststep] > minSOC and AvailableCapacityShed[n][laststep] > minCapacityShed:
                        NumDevicesToCall += 1          
#                print('devices to call',NumDevicesToCall,'request', fleet_load_request[step][0])
#                if fleet_load_request[step][1] < 0 and NumDevicesToCall > 0: #if shed is called for and there are some devices that can respond
#                    #first option below includes a fudge factor, second assumes that forecasting in the WH model for availability for the next timestep given aggregator-provided forecast water draws is accurate enough
#                    newrequest = fleet_load_request_total[step] / (NumDevicesToCall/9.5*np.exp(-numWH/20)+1) #9.5*exp(-numWH/20)+1 ad hoc curve fit based on trying numWH = 20,30,10,200 and doing hand curve fit. 
#                elif fleet_load_request[step][1] > 0 and NumDevicesToCall > 0: 
#                    newrequest = fleet_load_request_total[step] / (NumDevicesToCall/2) # easier to do load add, but some "available" devices still won't be able to respond so ask for 2x what you would expect 
#                else:
#                    newrequest = fleet_load_request_total[step]
                    
                fleet_load_request[step] = [fleet_load_request[step][0],fleet_load_request_total[step] / max(NumDevicesToCall,1)]
        
        
        
            for wh in whs: #loop through water heatesr
                if step == 0:
                    ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailableAdd, isAvailableShed, elementon = wh.execute(TtankInitial[number], TsetInitial[number], Tamb[number][0], RHamb[number][0], Tmains[number][0], draw[number][0], fleet_load_request[0], ServiceCallsAccepted[number][0], elementOn[number][0], addshedTimestep, draw_fleet_ave[0])
                else:
                    
                    TsetLast = Tset[number][laststep]
                    TtankLast = Ttank[number][laststep]                    
                    ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailableAdd, isAvailableShed , elementon = wh.execute(TtankLast, TsetLast, Tamb[number][step], RHamb[number][step], Tmains[number][step], draw[number][step], fleet_load_request[step], ServiceCallsAccepted[number][laststep], elementOn[number][laststep], addshedTimestep, draw_fleet_ave[min([step+1,Steps])]) #min([step+1,Steps]) is to provide a forecast for the average fleet water draw for the next timestep while basically ignoring the last timestep forecast

#                assign returned parameters to associated lists to be recorded
                Tset[number][step] = tset
                Ttank[number][step] = ttank
                dTtank_set [number][step] = ttank - tset
                SoC[number][step] = soC
                IsAvailableAdd[number][step] = isAvailableAdd
                IsAvailableShed[number][step] = isAvailableShed
                elementOn[number][step] = elementon
                AvailableCapacityAdd[number][step] = availableCapacityAdd
                AvailableCapacityShed[number][step] = availableCapacityShed
                ServiceCallsAccepted[number][step] = serviceCallsAccepted
                ServiceProvided[number][step] = eservice
                servsum += eservice
                TotalServiceProvidedPerWH[number] = TotalServiceProvidedPerWH[number] + ServiceProvided[number][step]
                request += fleet_load_request[step][1] 
                number += 1

            TotalServiceProvidedPerTimeStep[step] += servsum 
        
        #####################################
#        This is only for regulation, essentially the same operations as above but recorded separately and using a different timestep
        if  fleet_load_request[step][0] == 'regulation':                
                
            for reg_step in range(lengthRegulation):
                NumDevicesToCall = 0
                servsumReg = 0
                #assume this won't be called unless step > 0
                number = 0 #need to reset since i'll be looping through a different timestep
                if reg_step == 0:
                    lastStep = laststep
                    #figure how many devices to call for the regulation service
                    for n in range(numWH):
                        if (IsAvailableAdd[n][lastStep] > 0 or IsAvailableShed[n][lastStep] > 0) > 0 and SoC[n][lastStep] > minSOC and SoC[n][lastStep] < maxSOC: #don't specify min capacity to be available for regulation
                            NumDevicesToCall += 1
                else:
                    lastStep = reg_step -1
                    #figure how many devices to call for the regulation service
                    n = 0
                    for n in range(numWH):
                        if (IsAvailableAddReg[n][lastStep] > 0 or IsAvailableShedReg[n][lastStep] > 0) > 0 and SoCReg[n][lastStep] > minSOC and SoCReg[n][lastStep] < maxSOC: #don't specify min capacity to be available for regulation
                            NumDevicesToCall += 1
                                
                
                #figure out how much to ask of each device
                if fleet_regulation_request[reg_step][1] != 0 and NumDevicesToCall > 0: 
                    newrequest = fleet_regulation_request[reg_step][1] / NumDevicesToCall #since timestep is small, assume that all devices available last step will be available for this step
                else:
                    newrequest = fleet_regulation_request[reg_step][1]
                        
                fleet_regulation_request[reg_step] = [fleet_regulation_request[reg_step][0],newrequest]
                
                for wh in whs: #loop through each water heater, assume won't be called unless step > 0        
                    if reg_step == 0:
                        TtankLast = Ttank[number][lastStep]
                    else:
                        TtankLast = TtankReg[number][lastStep]
                    
#                    call the water heater model
                    ttank, tset, soC, availableCapacityAdd, availableCapacityShed, serviceCallsAccepted, eservice, isAvailableAdd, isAvailableShed, elementon = wh.execute(TtankLast, TsetLast, Tamb[number][step], RHamb[number][step], Tmains[number][step], draw[number][step], fleet_regulation_request[reg_step], ServiceCallsAcceptedReg[number][lastStep], elementOnReg[number][lastStep], addshedTimestep, draw_fleet_ave[min([step+1,Steps])])

#                    save outputs in lists
                    TtankReg[number][reg_step] = ttank
                    SoCReg[number][reg_step] = soC
                    IsAvailableAddReg[number][reg_step] = isAvailableAdd
                    IsAvailableShedReg[number][reg_step] = isAvailableShed
                    elementOnReg[number][reg_step] = elementon
                    AvailableCapacityAddReg[number][reg_step] = availableCapacityAdd
                    AvailableCapacityShedReg[number][reg_step] = availableCapacityShed
                    ServiceCallsAcceptedReg[number][reg_step] = serviceCallsAccepted
                    ServiceProvidedReg[number][reg_step] = eservice
                    servsumReg += eservice
                    TotalServiceProvidedPerWHReg[number] = TotalServiceProvidedPerWHReg[number] + ServiceProvidedReg[number][reg_step]

                    if reg_step == lengthRegulation-1: # save variables to change back to load add/shed timesteps
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
                    number += 1
                TotalServiceProvidedPerTimeStepReg[reg_step] += servsumReg
                TotalServiceProvidedPerTimeStep[step] += servsum #update for the next step when no longer in regulation mode
                
                for n in range(number):
                    TotalServiceCallsAcceptedPerWHReg[n] = ServiceCallsAcceptedReg[n][reg_step]
                
    for n in range(number):
        TotalServiceCallsAcceptedPerWH[n] = ServiceCallsAccepted[n][step]


############################################################################
#   Plotting load add/shed responses
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
    plt.plot(TotalServiceProvidedPerTimeStep[0:20],'r*-',label='Provided by Fleet')
    plt.plot(fleet_load_request_total[0:20],'bs-', label ='Requested')
    plt.ylabel('Total Service During Timestep, W')
    plt.xlabel('step')
    plt.legend()
    plt.show()
    
    plt.figure(7)
    plt.clf()
    plt.hist(TotalServiceCallsAcceptedPerWH)
    plt.xlabel('Total Service Calls Accepted per WH Annually')
    plt.show()
        
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
    
    plt.figure(19)
    plt.clf()
    plt.hist(TtankInitial)
    plt.xlabel('Tank Temperature Initial [deg F]')
    plt.show()
    
    plt.figure(20)
    plt.clf()
    plt.hist(TsetInitial)
    plt.xlabel('Tank Setpoint Temperature Initial [deg F]')
    plt.show()
    
    plt.figure(21)
    plt.clf()
    plt.hist(Capacity)
    plt.xlabel('Tank Capacity [gal]')
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

###############################################################################    
# from Jeff Maguire annual_ewh_run.py on December, 11, 2017
# modifications by CWB, eliminate 'self', eliminated 'initial_time' 
    
def get_annual_conditions(climate_location, installation_location, days_shift,n_br,unit,timestep_min):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
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
                agghotflow += hot_flow
                aggmixflow += mixed_flow
#                aggregate whenever the linenum is a multiple of timestep_min. Each increment in lineum represents one minute. Timestep_min is the number of minutes per timestep
                if linenum % timestep_min == 0: 
                    hot_draw[draw_idx] = agghotflow
                    mixed_draw[draw_idx] = aggmixflow
                    agghotflow = 0
                    aggmixflow = 0
                    draw_idx += 1
            linenum += 1
            if draw_idx >= steps_per_year:
                draw_idx = 0
        draw_profile_file.close()
        return Tamb, RHamb, Tmains, hot_draw, mixed_draw




if __name__ == '__main__':
    main()