from datetime import datetime, timedelta
import numpy
from fleet_request import FleetRequest
#from fleet_response import FleetResponse
from battery_inverter_fleet import BatteryInverterFleet

def fleet_test():
    Fleet = BatteryInverterFleet()

    t = numpy.linspace(0, 24, 97)

    requests = []
    ts = datetime.utcnow()
    dt = 1/4 #hours
    for i in t:
        req = FleetRequest(ts,dt,float(10*numpy.sin(2*numpy.pi*i/24)),0.0)
        requests.append(req)

    # print the initial SoC
    print("SoC =", str(Fleet.soc))
    FORCAST = Fleet.forecast(requests) # generate a forecast 
    print("SoC =", str(Fleet.soc))
    # make sure that the forecast function does not change the SoC

    # print the forecasted achivable power schedule
    for i in range(97):
        rsp = FORCAST[i]
        print("P =", str(rsp.P_injected))

    # process the requests 
    for req in requests:
        Fleet.process_request(req.sim_step, req.P_req, req.Q_req)
        print("SoC =", str(Fleet.soc)) # show that process_request function updates the SoC


def integration_test():

    # Establish the test variables
    n = 24
    dt = 1
    SoC0 = 50
#    t = numpy.linspace(0, (n - 1), n)
    EffMatrix = numpy.zeros((n, n))
    ts = datetime.utcnow()
    print(n)

    for i in numpy.arange(0, n):
        for j in numpy.arange(0, n):
            if i != j:
                Fleet = BatteryInverterFleet()
                Fleet.soc = SoC0  # initialize SoC
                Power = numpy.zeros(n)  # initialize Power
                Power[i] = Fleet.max_power_charge
                Power[j] = Fleet.max_power_discharge
                # simulate the system with SoC0 and Power requests
                for T in numpy.arange(0, n):
                    req = FleetRequest(ts,dt,Power[T],0.0)
                    Fleet.process_request(req.sim_step, req.P_req, req.Q_req)
                
                SoCFin = Fleet.soc  # get final SoC
                [P2, Cost, Able] = Fleet.cost(SoCFin, SoC0, dt)  # retreeve how much power it would take to return to SoC0
                P2Charge = max(P2,0)
                P2Discharge = min(P2,0)
                EffMatrix[i, j] = -(Power[j] +P2Discharge)/ (
                            Power[i] + P2Charge)  # calculate efficiency      DISCHARGE_ENERGY / CHARGE_ENERGY
                if P2<0:
                    print('err')
                if Able == 0:
                    EffMatrix[i, j] = 0

    print(EffMatrix)


if __name__ == '__main__':
    fleet_test()
    integration_test()


