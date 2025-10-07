from esa import SAW
import numpy as np
import os, sys
import csv
from csv import reader
def setup_voltage_data(pw):
    pw.runScriptCommand('SolvePowerFlow(RECTNEWT)')
    Bus_data=pw.getParametersMultipleElement('Bus', ['BusNum','BusKVVolt'])
    BusKV=Bus_data[1]
    BusKV=np.asarray(BusKV)
    BusKV=np.asfarray(BusKV,float)
    #BusKV=BusKV.tolist()
    return BusKV

def compile_power(pw,Power):
    #get data into correct format
    DSS=Power
    Data1=DSS[DSS.find('['):]
    Data1=Data1[1:-1]
    power=Data1.split(";")
    Power_data=[]
    for item in power:
        if item!='':
            Power_data.append(float(item))
    P=[]
    Q=[]
    i=0;
    while i<(len(Power_data)-1):
        j=i+1
        P.append(Power_data[i]/1E3)
        Q.append(Power_data[j]/1E3)
        i=i+2
    Ptotal=0
    Qtotal=0
    if len(power)>2:
        Ptotal=np.sum(P)
        Qtotal=np.sum(Q)
    return Ptotal, Qtotal

def update_power(pw,P,Q,Bus):
    #pw.runScriptCommand('SolvePowerFlow(RECTNEWT)')
    '''
    if not os.path.exists(opf_path):
        os.makedirs(opf_path)
    opf_file = opf_path + f"\\opf_data_X{hour}"
    pw.RunScriptCommand(f'SolvePrimalLP("{opf_file}")')
    '''
    pw.RunScriptCommand(f'SolvePrimalLP()')
    Load_data=pw.getParametersMultipleElement('Load', ['BusNum','LoadID'])
    fed_name=["distribution_system_bus2_feeder1_substation_voltage","distribution_system_bus2_feeder2_substation_voltage","distribution_system_bus3_feeder1_substation_voltage","distribution_system_bus3_feeder2_substation_voltage"]
    BusNum=Load_data[0]
    Numbers=np.asarray(BusNum)
    Bus_Num=[]
    '''
    R=[]
    for item in Bus:
        newstr = ''.join((ch if ch in '0123456789' else ' ') for ch in item)
        listOfNumbers = [int(i) for i in newstr.split()]
        R.append(listOfNumbers)
    '''    
    for item in Numbers:
        Bus_Num.append(int(item))
    ID=Load_data[1]
    dist_bus=[]
    P_load=np.zeros(len(P))
    Q_load=np.zeros(len(Q))
    for i in range(len(BusNum)):
        feed="bus"+str(Bus_Num[i])
        dist_bus.append(feed)
    for i in range(len(BusNum)):
        for j in range(len(P)):
            if(dist_bus[i] in fed_name[j]):
                P_load[i]=P_load[i]+P[j]
                Q_load[i]=Q_load[i]+Q[j]

    ObjectType='Load'
    Paramlist=['BusNum', 'ID', 'LoadSMW', 'LoadSMVR']
    for i in range(0,2):
        ValueArray=[BusNum[i], ID[i], P_load[i], Q_load[i]]
        pw.changeParameters(ObjectType, Paramlist,ValueArray)
    return  

def csv_reader(master_csv):
    rowcount = -2
    rowslist = []
    with open(master_csv) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter='\t')
        for row in csv_reader:
            rowcount += 1;
            if rowcount >= 0:
                rowslist.append(row)
    Bus=[]
    for row in rowslist:
        number=row[7]
        Bus.append(number)
    return Bus
    
