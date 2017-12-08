import numpy
import scipy
import csv
import os
import math
from math import pi
import matplotlib.pyplot as plt
import time
import numpy as np
import basic_water_heater
from scipy.stats import norm

class WaterHeater():
    def __init__(self):
        #Declare constants
        self.initial_time = time.time()
        self.timestep = 1.0 #minutes
        self.timestep_hour = self.timestep / 60.0 #hours
        self.timestep_sec = self.timestep * 60.0 #seconds
        self.water_Cp = 1.0007 # Btu/lb-F
        self.water_density = 8.2938 # lb/gal
        self.water_k = 0.34690 #Btu/hr-ft-F
        self.ft3_to_gal = 7.4805195 #ft^3 to gal unit conversion
        self.gal_to_in3 = 231 #gal to ft^3 unit conversion
        self.kw_to_btu_h = 3412.0 #Btu/h to kW unit conversion
        self.Tset = 125.0 #F
        self.Tdeadband = 10.0 #delta F
        Tmixed = 110.0 #F
        self.E_heat = 4.5 #kW
        self.tank_model = 'mixed' #can be either stratified or mixed
        if self.tank_model == 'stratified':
            self.n_nodes = 12
        else:
            self.n_nodes = 1
        self.phi = None
        self.gamma = None
        self.ctrl_ue = 0
        self.last_ue = self.ctrl_ue
        self.ctrl_le = 0
        self.last_le = self.ctrl_le
        
        #preserving these voltage things from GridLAB-D in case this model ever makes it back into there
        self.actual_voltage = 240.0 #V
        self.nominal_voltage = 240.0 #V
        self.climate_location = 'denver' #TODO: is location a climate zone, 
        self.installation_location = 'living' #Options are living, unfinished basement, garage, or attic 
        self.num_bedrooms = 3 #From 1-5
        self.unit_num = 0 #From 0-9
        self.days_shift = 180 #From 0-364
        if self.days_shift > 364:
            self.days_shift = self.days_shift % 365
            print('Days shifted is greater than 365, will use {} as the number of days shifted'.format(self.days_shift))
        #TODO: should we allow other location installations (finished basement, crawlspaces, outside?)
        #Load ambient conditions from files
        (Tamb, RHamb, Tmains, hot_draw, mixed_draw) = self.get_annual_conditions(self.days_shift,self.num_bedrooms,self.unit_num)

        #calculate water heater properties
        FHR = 65.0 #gal 
        UEF = 0.90 #Uniform Energy Factor
        V = 50.0 #gal
        ratings_test = 'UEF'
        
        (self.wh_UA, self.wh_eta_c, self.wh_vol) = self.calc_wh_properties(ratings_test,FHR,UEF,V)
        self.mCp_node = self.water_Cp * self.water_density * self.wh_vol / self.n_nodes
        m_node = self.water_density * self.wh_vol / self.n_nodes
        vol_inches = self.wh_vol * 231
        height = 48 # inches
        radius = ((pi * height) / vol_inches) ** 0.5
        A = 2 * pi * radius * (radius + height)
        U = self.wh_UA / A
        side_A = 2 * pi * height * radius
        self.end_A = 2 * pi * radius ** 2
        self.UA_node = U * (side_A / self.n_nodes)
        self.UA_end = self.UA_node + (U * self.end_A)
        self.L = height / self.n_nodes
        #Initialize timestep values
        T_amb_ts = 0.0
        RHamb_ts = 0.0
        Tmains_ts = 0.0
        draw_ts = 0.0
        if self.tank_model == 'stratified':
            Tlast = self.Tset * np.ones(self.n_nodes)
        else: #mixed tank
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
        days_run = 3
        hours_run = 24 * days_run
        for hour in range(hours_run):#8760 is 1 year, 744 is January, 168 is 1 week, 24 is 1 day
            T_amb_ts = float(Tamb[hour])
            RH_amb_ts = float(RHamb[hour])
            Tmains_ts = float(Tmains[hour])
            print('Starting hour {}'.format(hour + 1))
            for min in range(60):
                draw_ts = (60 * hour + min)
                draw = hot_draw[draw_ts] + mixed_draw[draw_ts] * ((Tmixed - Tmains_ts) / (Tlast - Tmains_ts)) #draw volume in gal
                #draw = hot_draw[draw_ts] + mixed_draw[draw_ts] #draw volume in gal, only draw hot water
                if self.tank_model == 'stratified':
                    (Ttank_ts,Econs_ts) = self.stratified_tank_ctrl(Tlast,T_amb_ts,Tmains_ts,draw,draw_ts,draw_ts)
                else:
                    (Ttank_ts,Econs_ts) = self.mixed_tank(Tlast,T_amb_ts,Tmains_ts,draw,draw_ts)
                Ttank.append(Ttank_ts)
                Vdraw.append(draw)
                Econs.append(Econs_ts)
                Edel_ts = draw * self.water_density * self.water_Cp * (Ttank_ts - Tmains_ts)
                Eloss_ts = self.wh_UA * (Ttank_ts - T_amb_ts)
                Edel.append(Edel_ts)
                Eloss.append(Eloss_ts)
                outputfile.write(str(T_amb_ts) + ',' + str(RH_amb_ts) + ',' + str(Tmains_ts) + ',' + str(draw) + ',' + str(Ttank_ts) + ',' + str(Econs_ts) + ',' + str(Edel_ts) + ',' + str(Eloss_ts) + '\n')
                Tlast = Ttank_ts
        self.time_finised = time.time()
        run_time_total = self.time_finised - self.initial_time
        print('Runs complete! Ran {} days.'.format(days_run))
        print('Total run time is {} seconds'.format(run_time_total))

    
    def get_annual_conditions(self,days_shift,n_br,unit):
        #reads from 8760 (or 8760 * 60) input files for ambient air temp, RH, mains temp, and draw profile and loads data into arrays for future use
        #TODO: RH is currently unused, will need to import some psych calculations to get a WB
        #TODO: Use a .epw weather file? We'll eventually need atmospheric pressure (for psych calcs), could also estimate unconditioned space temp/rh based on ambient or calc mains directly based on weather file info
        Tamb = []
        RHamb = []
        Tmains = []
        if self.climate_location != 'denver':
            raise NameError("Error! Only allowing Denver as a run location for now. Eventually we'll allow different locations and load different files based on the location.")
        if self.installation_location == 'living':
            amb_temp_column = 1
            amb_rh_column = 2
        elif self.installation_location == 'unfinished basement':
            amb_temp_column = 3
            amb_rh_column = 4
        elif self.installation_location == 'garage':
            amb_temp_column = 5
            amb_rh_column = 6
        elif self.installation_location == 'unifinished attic':
            amb_temp_column = 7
            amb_rh_column = 8
        else:
            raise NameError("Error! Only allowed installation locations are living, unfinished basement, garage, unfinished attic. Change the installation location to a valid location")
        mains_temp_column = 9
        
        linenum = 0
        
        ambient_cond_file = open((os.path.join(os.path.dirname(__file__),'data_files','denver_conditions.csv')),'r') #hourly ambient air temperature and RH
        for line in ambient_cond_file:
            if linenum > 0: #skip header
                items = line.strip().split(',')
                Tamb.append(float(items[amb_temp_column]))
                RHamb.append(float(items[amb_rh_column]))
                Tmains.append(float(items[mains_temp_column]))
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
                n_beds = float(items[0]) - 1
                n_unit = float(items[1])
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
        yr_min = 60 * 24 * 365
        hot_draw = np.zeros((yr_min,1))
        mixed_draw = np.zeros((yr_min,1))
        #take into account days shifted
        draw_idx = 60 * 24 * days_shift
        draw_profile_file = open((os.path.join(os.path.dirname(__file__),'data_files','DrawProfiles','DHWDrawSchedule_{}bed_unit{}_1min_fraction.csv'.format(n_br,unit))),'r') #minutely draw profile (shower, sink, CW, DW, bath)
        for line in draw_profile_file:
            if linenum > 0:
                items = line.strip().split(',')
                hot_flow = 0
                mixed_flow = 0
                if items[0] != '':
                    sh_draw = float(items[0]) * sh_max[n_br,unit] * (sh_hsp_tot / sh_sum[n_br,unit])
                    mixed_flow += sh_draw
                if items[1] != '':
                    s_draw = float(items[1]) * s_max[n_br,unit] * (s_hsp_tot / s_sum[n_br,unit])
                    mixed_flow += s_draw
                if items[2] != '':
                    cw_draw = float(items[2]) * cw_max[n_br,unit] * (cw_hsp_tot / cw_sum[n_br,unit])
                    hot_flow += cw_draw
                if items[3] != '':
                    dw_draw = float(items[3]) * dw_max[n_br,unit] * (dw_hsp_tot / dw_sum[n_br,unit])
                    hot_flow += dw_draw
                if items[4] != '':
                    b_draw = float(items[4]) * b_max[n_br,unit] * (b_hsp_tot / b_sum[n_br,unit])
                    mixed_flow += b_draw
                hot_draw[draw_idx] = hot_flow
                mixed_draw[draw_idx] = mixed_flow
            linenum += 1
            draw_idx += 1
            if draw_idx >= yr_min:
                draw_idx = 0
        draw_profile_file.close()
        time_draw_profile_completed = time.time()
        time_load_draw = time_draw_profile_completed - self.initial_time
        print("Loaded draw profile after {} seconds".format(time_load_draw))
        
        return Tamb, RHamb, Tmains, hot_draw, mixed_draw
    
    #Calculate water heater properties:
    def calc_wh_properties(self,ratings_test,FHR,UEF,V):
        if ratings_test == 'UEF':
            test_Tset = 125 #F
            test_Tin = 58 #F
            test_Tenv = 67.5 #F
            
            if FHR < 18:
                #Very Small Usage Draw Profile
                test_draw_volume = 10 #gal
            elif FHR < 51:
                #Small Usage Draw Profile
                test_draw_volume = 38 #gal
            elif FHR < 75:
                #Medium Usage Draw Profile
                test_draw_volume = 55 #gal
            else:
                #High Usage Draw Profile
                test_draw_volume = 84 #gal
                
            draw_mass = test_draw_volume * self.water_density
            test_Qload = draw_mass * self.water_Cp * (test_Tset - test_Tin)
            wh_vol = 0.9 * V #gal
            wh_eta_c = 1.0
            wh_UA = test_Qload * (1 / UEF - 1) / ((test_Tset - test_Tenv) * 24)
        elif ratings_test == 'EF':
             #calculates UA and conversion efficiency based on EF and volume using old EF test procedure
            #TODO: Update this for UEF
            test_volume_drawn = 64.3 # gal/day
            test_Tset = 135 # F
            test_Tin = 58 # F
            test_Tenv = 67.5 # F
            draw_mass = test_volume_drawn * self.water_density # lb
            test_Qload = draw_mass * self.water_Cp * (test_Tset - test_Tin) # Btu/day
            
            wh_vol = 0.9 * V #gal
            wh_eta_c = 1.0
            wh_UA = test_Qload * (1 / UEF - 1) / ((test_Tset - test_Tenv) * 24)
        else:
            raise NameError("Error! Invalid test selected. Pick either the EF or UEF test procedure")

        
        return wh_UA, wh_eta_c, wh_vol
    
    def mixed_tank(self,Tlast,T_amb_ts,Tmains_ts,draw,draw_ts):
        """ Calculate next temperature and load"""
        mCp = self.water_Cp * self.water_density * self.wh_vol
        
        #start by calculating what the tank temperature would be if the heat doesn't come on
        a = (1 / mCp) * (self.wh_UA * T_amb_ts + ((draw * 60) * self.water_density * self.water_Cp * Tmains_ts))
        b =(-1 / mCp) * (self.wh_UA + ((draw * 60) * self.water_density * self.water_Cp))
        Eheat_ts = 0
        Ttank = ((a/b)+Tlast) * math.exp(b * self.timestep_hour) - (a/b)
        if draw_ts == 0: #First timestep
            self.qheat_last = 0
        if (Ttank < (self.Tset - self.Tdeadband)) or (self.qheat_last > 0 and Ttank < self.Tset):
            self.qheat_last = 1
            #If the heat is needed, try the heat at full bore and see if the tank overheats
            a = (1 / mCp) * (self.E_heat * self.kw_to_btu_h + self.wh_UA * T_amb_ts + ((draw * 60) * self.water_density * self.water_Cp * Tmains_ts))
            b =(-1 / mCp) * (self.wh_UA + ((draw * 60) * self.water_density * self.water_Cp))
            Ttank = ((a / b) + Tlast) * math.exp(b * self.timestep_hour) - (a / b)
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
            
        
        
    def update_stratified_wh_temps(self,draw, timestep_sec):
        #Calculate matrix elements for A, B, and C
        #Refer to MATLAB WH control paper for more deails on how these matrices are set up
        elem_ua_mid_flow = -(UA_node + (draw * 60 * self.water_density * self.water_Cp)) / self.mCp_node
        elem_ua_end_flow = -(UA_end + (draw * 60 * self.water_density * self.water_Cp)) / self.mCp_node
        elem_draw = (draw * 60 * self.water_density * self.water_Cp) / self.mCp_node
        elem_ua_mid = self.UA_node / self.mCp_node
        elem_ua_end = self.UA_end / self.mCp_node 
        elem_input = (self.wh_eta_c * self.E_heat) / self.mCp_node
        
        Ac = np.array([elem_ua_end_flow, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [elem_draw, elem_ua_mid_flow, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, elem_draw, elem_ua_mid_flow, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, elem_draw, elem_ua_mid_flow, 0, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, elem_draw, elem_ua_mid_flow, 0, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, elem_draw, elem_ua_mid_flow, 0, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, elem_draw, elem_ua_mid_flow, 0, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, elem_draw, elem_ua_mid_flow, 0, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, elem_draw, elem_ua_mid_flow, 0, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, elem_draw, elem_ua_mid_flow, 0, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0, elem_draw, elem_ua_mid_flow, 0],
                      [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, elem_draw, elem_ua_end_flow],
                      dtype ='float')
        
        Bc = np.array([0, 0, elem_ua_end, elem_draw],
                      [0, 0, elem_ua_mid, 0],
                      [elem_input, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, elem_input, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_mid, 0],
                      [0, 0, elem_ua_end, 0],
                      dtype ='float')
        
        Cc = np.array([0,0],
                      [0,0],
                      [1,0],
                      [0,0],
                      [0,0],
                      [0,0],
                      [0,0],
                      [0,0],
                      [0,1],
                      [0,0],
                      [0,0],
                      [0,0],
                      dtype ='float')
                    
        n, nb = Ac.shape[1], Bc.shape[1]
        v = np.vstack((np.hstack((Ac,Bc)) * timestep_sec, np.zeros((nb,nb+n))))
        s = scipy.linalg.expm(v)
        self.phi, self.gamma =  s[0:n,0:n], s[0:n,n:n+nb]
        
        
    def stratified_tank_ctrl(self,Tlast,T_amb_ts,Tmains_ts,draw,draw_ts):
        #Control logic (master/slave) for electric resistance WH
        if T_upper < (self.Tset - self.Tdeadband):
            self.ctrl_ue = 1
        elif T_upper > self.Tset:
            self.ctrl_ue = 0
        elif last_ue == 1:
            self.ctrl_ue = self.last_ue
        if self.ctrl_ue != 1:
            if T_lower < (self.Tset - self.Tdeadband):
                self.ctrl_le = 1
            elif T_lower > self.Tset:
                self.ctrl_le = 0
            elif last_le == 1:
                self.ctrl_le = self.last_le
        self.last_ue = self.ctrl_ue
        self.last_le = self.ctrl_le
        wh.integrate(self, draw, Tmains_ts,T_amb_ts,self.ctrl_le,self,ctrl_ue,timestep_sec)#(self,Tlast,T_amb_ts,Tmains_ts,draw,draw_ts,draw_ts)
        
    def integrate(self, draw, Tmains_ts,T_amb_ts,ctrl_le,ctrl_ue,timestep_sec):
        """
        input:
            flow: [gal/min]
            mains_inlet_temp: [F]
            ambient_temp: [F]
            control_flag: [unitless]  {0:off, 1:node_1_on or 2:node_2_on}
            timestep_sec: [sec]

        output:
            None. The class variables T1 and T2 are updated internally.
        """

        self.update_stratified_wh_temps(draw, timestep_sec) 
        #integrate the state-space system
        for n in range(n_nodes):
            if n == 0:
                self.T[n] =     self.phi[n,n]   * self.T[n] + \
                                self.gamma[n,0] * control_1 + \
                                self.gamma[n,1] * control_2 + \
                                self.gamma[n,2] * ambient_temp + \
                                self.gamma[n,3] * mains_inlet_temp
                                
            else:
                self.T[n] =     self.phi[n,n]   * self.T[n] + \
                                self.phi[n,n-1]   * self.T[n-1] + \
                                self.gamma[n,0] * control_1 + \
                                self.gamma[n,1] * control_2 + \
                                self.gamma[n,2] * ambient_temp + \
                                self.gamma[n,3] * mains_inlet_temp
                
        for n in range(n_nodes): #check for temperature inversions, mix them out
            if n > 0:
                if T[n-1] > T[n]:
                    T[n] = (T[n-1] + T[n]) / 2
                    T[n-1] = T[n]
 
            
        #new_T_noElem = self.phi[,]
        
        
        #new_T2 =    self.phi[1,0]   * self.T1 + \
        #            self.phi[1,1]   * self.T2 + \
        #            self.gamma[1,0] * control_1 + \
        #            self.gamma[1,1] * control_2 + \
        #            self.gamma[1,2] * ambient_temp +\
        #            self.gamma[1,3] * mains_inlet_temp
        
        #self.
        #self.T1 = new_T1
        #self.T2 = new_T2
        
        '''    
            self.q_draw = np.zeros(self.n_nodes)
            self.q_mix = np.zeros(self.n_nodes)
            self.q_tankloss = np.zeros(self.n_nodes)
            self.q_cond = np_zeros(self.n_nodes)
            self.mdot_mix = 0.5 *(m_node / (60))
        for n in range(n_nodes):
            #Heat transfered due to draw
            if n == 0:
                q_draw[n] = (draw * 60 * self.water_Cp * (Tmains_ts - Ttank[n])) + (draw * 60 * self.water_Cp * (Ttank[n] - Ttank[n+1]))
            elif n == (n_nodes - 1):
                q_draw[n] = (draw * 60 * self.water_Cp * (Ttank[n-1] - Ttank[n])) + (draw * 60 * self.water_Cp * (Ttank[n] - Ttank[n+1]))
            else:
                q_draw[n] = (draw * 60 * self.water_Cp * (Ttank[n-1] - Ttank[n])) + (draw * 60 * self.water_Cp * (Ttank[n+1] - Ttank[n]))
                
            #Heat transferred due to tank losses
            if n == 0 or n == (n_nodes - 1):
                q_tankloss[n] = (self.UA_node + self.UA_end) * (Ttank[n] - T_amb_ts)
            else:
                q_tankloss[n] = self.UA_node * (Ttank[n] - T_amb_ts)
                
            #Heat transferred due to conduction
            if n == 0:
                q_cond[n] = ((self.water_k * self.end_A) / self.L) * (Ttank[n] - Ttank[n+1])
            elif n == (n_nodes - 1):
                q_cond[n] = ((self.water_k * self.end_A) / self.L) * (Ttank[n-1] - Ttank[n]) + ((self.water_k * self.end_A) / self.L) * (Ttank[n] - Ttank[n+1])
            else:
                q_cond[n] = ((self.water_k * self.end_A) / self.L) * (Ttank[n-1] - Ttank[n])
            
            #heat transferred due to mixing
            if n == 0:
                q_mix[n] = self.mdot_mix * 60 * self.water_Cp * (Ttank[n] - Ttank[n+1])
            elif n == (n_nodes - 1):
                q_mix[n] = (self.mdot_mix * 60 * self.water_Cp * (Ttank[n-1] - Ttank[n])) + (self.mdot_mix * 60 * self.water_Cp * (Ttank[n] - Ttank[n+1]))
            else:
                q_mix[n] = self.mdot_mix * 60 * self.water_Cp * (Ttank[n-1] - Ttank[n])
            
            if n == 0 or n == (n_nodes - 1):
                UA_node = wh_UA_end
            else:
                UA_node = wh_UA_node
            q_loss_n = UA_node * (T_amb_ts - T_n)
            
            
        
        
        #start by calculating what the tank temperature would be if the heat doesn't come on
        a = (1 / mCp) * (self.wh_UA * T_amb_ts + ((draw * 60) * self.water_density * self.water_Cp * Tmains_ts))
        b =(-1 / mCp) * (self.wh_UA + ((draw * 60) * self.water_density * self.water_Cp))
        Eheat_ts = 0
        Ttank = ((a/b)+Tlast) * math.exp(b * self.timestep_hour) - (a/b)
        if draw_ts == 0: #First timestep
            self.qheat_last = 0
        if (Ttank < (self.Tset - self.Tdeadband)) or (self.qheat_last > 0 and Ttank < self.Tset):
            self.qheat_last = 1
            #If the heat is needed, try the heat at full bore and see if the tank overheats
            a = (1 / mCp) * (self.E_heat * self.kw_to_btu_h + self.wh_UA * T_amb_ts + ((draw * 60) * self.water_density * self.water_Cp * Tmains_ts))
            b =(-1 / mCp) * (self.wh_UA + ((draw * 60) * self.water_density * self.water_Cp))
            Ttank = ((a / b) + Tlast) * math.exp(b * self.timestep_hour) - (a / b)
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
if __name__ == '__main__':
    wh = WaterHeater()