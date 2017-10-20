#!/usr/bin/env python
import numpy as np
import scipy.linalg
from pprint import pformat

class WaterHeater(object):
    def __init__(self, wh_p=4.5, ua=0.0019678, eta=1, t2=49, d=0.55, h=1.0):
        """
        WaterHeater class initialization parameters
        wh_p [kJ/sec] rated power of water heater
        ua   [kJ/(sec C)] = 7.084 kJ/hr-C
        eta  [none] recovery efficiency
        t2   [C] initial temperature of top node in Celsius
        d    [m] tank diameter in meters
        h    [m] tank height in meters

        Usage:
        The WaterHeater class provides the integrate method which will update
        the dynamic state space model with the given input variables and timestep

        
        wh=WaterHeater()
        for i in range(100):
            wh.integrate(0.01, 18, 25, 1, 1)

        """
        self.WH_P = wh_p                                                        #[kJ/sec] rated power of water heater
        self.UA = ua                                                            #[kJ/(sec C)] = 7.084 kJ/hr-C
        self.eta_c = eta                                                        #[none] recovery efficiency
        self.T2 = t2                                                            #[C] initial temperature of top node in Celsius
        self.diameter = d                                                       #[m] tank diameter in meters
        self.height = h                                                         #[m] tank height in meters
        self.T1 = self.T2 - 1                                                   #[C] bottom node temperature
        self.Cp = 4.1818                                                        #[kJ/(kg C)] heat capacity of water
        self.D = 1000                                                           #[kg/m^3] density of water
        self.volume =  self.height * np.pi * (self.diameter / 2)**2             #[m^3]
        self.S_top = 0.25 * np.pi * self.diameter**2                            #[m^2] top area
        self.S_side = np.pi * self.diameter * self.height                       #[m^2] side area
        self.S_total = self.S_top  * 2 + self.S_side                            #[m^2] total area
        self.UA1 = self.UA*(self.S_top+(2./3.)*self.S_side)/self.S_total        #bottom UA
        self.UA2 = self.UA*(self.S_top+(1./3.)*self.S_side)/self.S_total        #top UA
        self.C1 = self.volume * (2./3.) * self.D * self.Cp                      #bottom
        self.C2 = self.volume * (1./3.) * self.D * self.Cp                      #top
        self.phi, self.gamma = None, None
    
    def __repr__(self):
        return pformat({ 'node_temperatures':[self.T1,self.T2]})
    
    def __update_model__(self, flow, timestep_sec):
        #state space model matrix construction
        a00 = -(self.UA1 + flow * self.Cp) / self.C1
        a10 = flow * self.Cp / self.C2
        a11 = -(self.UA2 + flow * self.Cp) / self.C2
        Ac = np.array([[a00, 0], [a10, a11]], dtype = 'float')
        b00 = self.eta_c * self.WH_P / self.C1
        b02 = self.UA1 / self.C1
        b03 = flow * self.Cp / self.C1
        b11 = self.eta_c * self.WH_P / self.C2
        b12 = self.UA2 / self.C2
        Bc = np.array([[b00, 0, b02, b03], [0, b11, b12, 0]], dtype = 'float')
        #create discrete-time state-space system: 
        n, nb = Ac.shape[1], Bc.shape[1]
        v = np.vstack((np.hstack((Ac,Bc)) * timestep_sec, np.zeros((nb,nb+n))))
        s = scipy.linalg.expm(v)
        self.phi, self.gamma =  s[0:n,0:n], s[0:n,n:n+nb]
    
    def integrate(self, flow, mains_inlet_temp, ambient_temp, control_flag, timestep_sec = 1):
        """
        input:
            flow: [L/sec]
            mains_inlet_temp: [C]
            ambient_temp: [C]
            control_flag: [unitless]  {0:off, 1:node_1_on or 2:node_2_on}
            timestep_sec: [sec]

        output:
            None. The class variables T1 and T2 are updated internally.
        """
        control_1 = 1 if control_flag == 1 else 0
        control_2 = 1 if control_flag == 2 else 0
        if control_1 + control_2 > 1.0: raise ValueError("control_1 and control_2 must sum to less than 1")
        self.__update_model__(flow, timestep_sec) 
        #integrate the state-space system
        new_T1 =    self.phi[0,0]   * self.T1 + \
                    self.phi[0,1]   * self.T2 + \
                    self.gamma[0,0] * control_1 + \
                    self.gamma[0,1] * control_2 + \
                    self.gamma[0,2] * ambient_temp + \
                    self.gamma[0,3] * mains_inlet_temp
        new_T2 =    self.phi[1,0]   * self.T1 + \
                    self.phi[1,1]   * self.T2 + \
                    self.gamma[1,0] * control_1 + \
                    self.gamma[1,1] * control_2 + \
                    self.gamma[1,2] * ambient_temp +\
                    self.gamma[1,3] * mains_inlet_temp
        self.T1 = new_T1
        self.T2 = new_T2


if __name__ == '__main__':
    wh=WaterHeater()
    #testing water heater operation with deadband controller
    tset=49
    db=9.5
    y1,y2=[],[]
    last_control = this_control = 0
    for i in range(3600):
        if i==0: pass
        else:
            if wh.T2<tset-db:
                this_control = 2
            elif wh.T2>tset: 
                this_control = 0
            elif last_control == 2:
                this_control = last_control
            if this_control != 2: 
                if wh.T1<tset-db:
                    this_control = 1
                elif wh.T1>tset:
                    this_control = 0
                elif last_control==1:
                    this_control = last_control
        last_control = this_control
        wh.integrate(0.05, 18, 25, this_control, 1)
        y1.append(wh.T1)
        y2.append(wh.T2)
    
    import matplotlib.pyplot as plt
    import time
    fig=plt.figure()
    ax=plt.subplot(111)
    ax.plot(y1)
    ax.plot(y2)
    plt.show()
    time.sleep(10)

