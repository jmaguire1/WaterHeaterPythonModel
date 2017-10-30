import numpy
import scipy
import csv
import os
import math
from math import pi
import matplotlib.pyplot as plt
import time
import basic_water_heater

class WaterHeater():
    def __init__(self):
        #Declare constants
        self.timestep = (1/60.0) #hours
        self.water_Cp = 1.0007 # Btu/lb-F
        self.water_density = 8.2938 # lb/gal
        self.ft3_to_gal = 7.4805195 #ft^3 to gal unit conversion
        self.gal_to_in3 = 231 #gal to ft^3 unit conversion
        self.kw_to_btu_h = 3412.0 #Btu/h to kW unit conversion
        self.Tset = 125.0 #F
        self.Tdeadband = 10.0 #delta F
        Tmixed = 110.0 #F
        self.E_heat = 4.5 #kW
        #preserving these voltage things from GridLAB-D in case this model ever makes it back into there
        self.actual_voltage = 240.0 #V
        self.nominal_voltage = 240.0 #V
        
        #Load ambient conditions from files
        (Tamb, RHamb, Tmains, hot_draw, mixed_draw) = self.get_annual_conditions()
        
        #calculate water heater properties
        EF = 0.91 #Energy Factor
        V = 50.0 #gal
        (self.wh_UA, self.wh_eta_c, self.wh_vol) = self.calc_wh_properties(EF,V)
        self.mCp_tank = self.water_Cp * (self.water_density * self.ft3_to_gal) * self.wh_vol
        #Initialize timestep values
        T_amb_ts = 0.0
        RHamb_ts = 0.0
        Tmains_ts = 0.0
        draw_ts = 0.0
        Tlast = self.Tset
        
        #Initialize arrays for the outputs: tank avg temperature, water flow rate, tank consumed energy, tank delivered energy
        Ttank = []
        Vdraw = []
        Econs = []
        Edel = []
        Eloss = []
        outputfile = open((os.path.join(os.path.dirname(__file__),'ElecWHOutput.csv')),'w')
                          
        outputfile.write('T_amb (F), RH_amb (%), Tmains (F), Draw Volume(gal), T_tank (F), E_consumed (Btu), E_delivered (Btu), E_tankloss (Btu) \n')
        
        #Perform minutely calculations
        for hour in range(168):#8760 is 1 year
            T_amb_ts = float(Tamb[hour])
            RH_amb_ts = float(RHamb[hour])
            Tmains_ts = float(Tmains[hour])
            for min in range(60):
                draw_ts = (60 * hour + min)
                draw = hot_draw[draw_ts] + mixed_draw[draw_ts] * ((Tmixed - Tmains_ts) / (Tlast - Tmains_ts)) #draw volume in gal
                #draw = hot_draw[draw_ts] + mixed_draw[draw_ts] #draw volume in gal, only draw hot water
                (Ttank_ts,Econs_ts) = self.execute(Tlast,T_amb_ts,Tmains_ts,draw,draw_ts)
                Ttank.append(Ttank_ts)
                Vdraw.append(draw)
                Econs.append(Econs_ts)
                Edel_ts = draw * self.water_density * self.water_Cp * (Ttank_ts - Tmains_ts)
                Eloss_ts = self.wh_UA * (Ttank_ts - T_amb_ts)
                Edel.append(Edel_ts)
                Eloss.append(Eloss_ts)
                outputfile.write(str(T_amb_ts) + ',' + str(RH_amb_ts) + ',' + str(Tmains_ts) + ',' + str(draw) + ',' + str(Ttank_ts) + ',' + str(Econs_ts) + ',' + str(Edel_ts) + ',' + str(Eloss_ts) + '\n')
                Tlast = Ttank_ts
                
            
        #fig=plt.figure()
        #ax=plt.subplot(111)
        #ax.plot(Ttank_ts)
        #ax.plot(Econs_ts)
        #plt.show()
        #time.sleep(10)

    
    def get_annual_conditions(self):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        #TODO: RH is currently unused, will need to import some psych calculations to get a WB
        #TODO: Use a .epw weather file? We'll eventually need atmospheric pressure (for psych calcs), could also estimate unconditioned space temp/rh based on ambient or calc mains directly based on weather file info
        Tamb = []
        RHamb = []
        linenum = 0
        ambient_cond_file = open((os.path.join(os.path.dirname(__file__),'data_files','ambient.csv')),'r') #hourly ambient air temperature and RH
        for line in ambient_cond_file:
            if linenum > 0: #skip header
                items = line.strip().split(',')
                Tamb.append(float(items[0]))
                RHamb.append(float(items[1]))
            linenum += 1
        ambient_cond_file.close()
        
        linenum = 0
        Tmains = []
        mains_temp_file = open((os.path.join(os.path.dirname(__file__),'data_files','tmains.csv')),'r') #hourly inlet water temperature
        for line in mains_temp_file:
            if linenum > 0:
                items = line.strip().split(',')
                Tmains.append(float(items[0]))
            linenum += 1
        mains_temp_file.close()
        
        linenum = 0
        hot_draw = []
        mixed_draw = []
        draw_profile_file = open((os.path.join(os.path.dirname(__file__),'data_files','draw.csv')),'r') #minutely draw profile (shower, sink, CW, DW, bath)
        for line in draw_profile_file:
            if linenum > 0:
                items = line.strip().split(',')
                sh_draw = float(items[0])
                s_draw = float(items[1])
                cw_draw = float(items[2])
                dw_draw = float(items[3])
                b_draw = float(items[4])
                hot_flow = cw_draw + dw_draw
                mixed_flow = sh_draw + s_draw + b_draw
                hot_draw.append(hot_flow)
                mixed_draw.append(mixed_flow)
            linenum += 1
        draw_profile_file.close()
        
        return Tamb, RHamb, Tmains, hot_draw, mixed_draw
    
    #Calculate water heater properties:
    def calc_wh_properties(self,EF,vol):
        #calculates UA and conversion efficiency based on EF and volume using old EF test procedure
        #TODO: Update this for UEF
        test_volume_drawn = 64.3 # gal/day
        test_Tset = 135 # F
        test_Tin = 58 # F
        test_Tenv = 67.5 # F
        draw_mass = test_volume_drawn * self.water_density # lb
        test_Qload = draw_mass * self.water_Cp * (test_Tset - test_Tin) # Btu/day
        
        wh_vol = 0.9 * vol #gal
        wh_vol_inches = wh_vol * 231
        wh_height = 48 # inches
        wh_radius = ((pi * wh_height) / wh_vol_inches) ** 0.5
        wh_A = 2 * pi * wh_radius * (wh_radius + wh_height)
        wh_eta_c = 1.0
        wh_UA = test_Qload * (1 / EF - 1) / ((test_Tset - test_Tenv) * 24)
        wh_U = wh_UA / wh_A
        
        return wh_UA, wh_eta_c, wh_vol
    
    def execute(self,Tlast,T_amb_ts,Tmains_ts,draw,draw_ts):
        """ Calculate next temperature and load"""
        mCp = self.water_Cp * self.water_density * self.wh_vol
        
        #start by calculating what the tank temperature would be if the heat doesn't come on
        a = (1 / mCp) * (self.wh_UA * T_amb_ts + ((draw * 60) * self.water_density * self.water_Cp * Tmains_ts))
        b =(-1 / mCp) * (self.wh_UA + ((draw * 60) * self.water_density * self.water_Cp))
        Eheat_ts = 0
        Ttank = ((a/b)+Tlast) * math.exp(b * self.timestep) - (a/b)
        if draw_ts == 0: #First timestep
            self.qheat_last = 0
        if (Ttank < (self.Tset - self.Tdeadband)) or (self.qheat_last > 0 and Ttank < self.Tset):
            self.qheat_last = 1
            #If the heat is needed, try the heat at full bore and see if the tank overheats
            a = (1 / mCp) * (self.E_heat * self.kw_to_btu_h + self.wh_UA * T_amb_ts + ((draw * 60) * self.water_density * self.water_Cp * Tmains_ts))
            b =(-1 / mCp) * (self.wh_UA + ((draw * 60) * self.water_density * self.water_Cp))
            Ttank = ((a / b) + Tlast) * math.exp(b * self.timestep) - (a / b)
            Eheat_ts = self.E_heat * self.kw_to_btu_h / 60 #Btu
            if Ttank > self.Tset:
                #If the tank overheats, calculate how much heat is needed to actually maintain the setpoint
                t_heat = (1 / b) *  math.log(((a / b) + self.Tset)/((a / b) + Tlast))
                Eheat_ts = t_heat * (self.E_heat * self.kw_to_btu_h)/60
                Ttank = self.Tset
                self.qheat_last = 0
        else:
            self.qheat_last = 0
            
        if Ttank < Tmains_ts:
            debug = 1

        return Ttank, Eheat_ts
                
        '''
        mdot_Cp = self.water_Cp * draw_ts * 60 * self.water_density
        c1 = (self.tank_ua + mdot_Cp) / mCp_tank
        actual_kW = (self.heat_needed * self.E_heat * (self.actual_voltage ** 2) / (self.nominal_voltage ** 2))
        c2 = (actual_kW * self.btu_h_to_kW + mdot_Cp * self.inlet_temp + self.tank_ua * ambient_temp) / (self.tank_ua + mdot_Cp)
        new_temp = c2 - (c2 - self.current_temperature) * math.exp(-c1 * delta_t)
        #internal_gain = self.tank_ua * (new_temp - ambient_temp);
        Tlower = self.Tset - self.Tdeadband
        Tupper = self.Tset
    
        if( new_temp <= Tlower + 0.02):
            self.heat_needed = 1
        elif( new_temp >= Tupper - 0.02):
            self.heat_needed = 0
    
        self.current_temperature = new_temp
        return new_temp, actual_kW
        '''
   
if __name__ == '__main__':
    wh = WaterHeater()