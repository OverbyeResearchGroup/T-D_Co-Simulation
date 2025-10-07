# -*- coding: utf-8 -*-
import sys
import os
from saw_editing_file import SAW
import csv
import numpy as np
import tkinter as tk
from tkinter import simpledialog
import pandas as pd
from power_world_setup import setup_voltage_data, update_power, compile_power, csv_reader, check_convergence, weather_gen
import ast

# Hack to add helics_utils to path
# TODO: use setup.py instead
CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, ".."))

from helics_utils import Federate, setup_helics_federate

def get_weather_buses():
    weather_data = pd.read_csv(CURRENT_DIRECTORY + f'\\weather\\renewable_generation_{date}.csv')
    weather_data = weather_data[weather_data.eq(f'6/8/2021  {time}:00:00 {set}').any(1)]
    weatherName = weather_data['GenName']
    GenP = weather_data['MaxMW']
    dt = weather_data['DateTime']
    gen_data = pw.GetParametersMultipleElement('Gen', ['BusNum', 'AreaName', 'BusName', 'GenID', 'GenStatus', 'GenMW',
                                                       'GenMVR', 'GenMWMin', 'GenMWMax', 'GenMVRMin', 'GenMVRMax'])
    gen_bus=gen_data['BusName']
    match_name=[0]*len(weatherName)
    ind=0
    for g in weatherName:
       for b in gen_bus:
           if b in g:
               match_name[ind]=b
       ind=ind+1
    weather_data['GenNamepw']=match_name
    weather_data.to_csv(CURRENT_DIRECTORY+f'\\weather\\renewable_generation_{date}.csv')

system="EV"
percent=""

weather=True
date='Aug. 6'

if date == 'Oct 16':
    start=6912
    full_date = '10/16/2021'
else:
    start=5208
    full_date = '8/6/2021'

CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))
PARENT_DIRECTORY=os.path.realpath(os.path.dirname(CURRENT_DIRECTORY))
pw_file="Texas7k_20221101_WithPFWModels_loadscaledmidnight.pwb"
master_pw=os.path.join(CURRENT_DIRECTORY,pw_file)
#master_pw=pw_file
pw=SAW(master_pw)

substation_list=pd.read_csv(PARENT_DIRECTORY + "\\dummy_list_mapped_system.csv")
IDs=substation_list["Substation Number"].values

timeseriesMW=pd.read_csv(CURRENT_DIRECTORY + f"\\MWtimeseries_{date}.csv")
timeseriesMVAR=pd.read_csv(CURRENT_DIRECTORY + f"\\MVARtimeseries_{date}.csv")

if weather==True:
    opf_path = PARENT_DIRECTORY + f'\\Co-Simulation-Results\\{date}\\{percent}\\Weather_data_added\\OPF'
else:
    opf_path = PARENT_DIRECTORY + f'\\Co-Simulation-Results\\{date}\\{percent}\\OPF'

#print(subID)

if __name__ == "__main__":
    
    federate = setup_helics_federate(
        federate_name=f"transmission_system",
        subscriptions=[f"transmission_system_load"],
        publications=[
            (f"distribution_system_voltage", "vector")
        ],

    )
    
    advance=0
    federate.advance(advance)
    #federate=setup_helics_federate(f"transmission_system", subscriptions, publications)
    print("running transmission system")
    hour_count=[]
    for i in range(1, 25):
        hour_count.append(i)

    hour=0
    for hour in hour_count:
        BusKV=setup_voltage_data(pw, IDs)
        BusKV = BusKV.tolist()
        #BusKV=[1,2,3,4,5]
        advance=advance+1
        #federate.advance(advance)
        BusKV=[advance, advance]

        #hour=hour+1
        if hour==1:
            time=12
            set='AM'
        elif hour==24:
            time=12
            set='PM'
        elif hour<11:
            time=hour+1
            set="AM"
        else:
            time = hour + 1
            set = "PM"
        MW=timeseriesMW['X'+str(hour)]
        MVAR=timeseriesMVAR['X'+str(hour)]
        Ldata = pw.GetParametersMultipleElement('load', ['BusNum', 'LoadID', 'LoadMW', 'LoadMVR'])
        Ldata['LoadMW']=MW
        Ldata['LoadMVR']=MVAR
        pw.change_and_confirm_params_multiple_element(ObjectType='load', command_df=Ldata)
        #pw.SolvePowerFlow()

        weather_data=pd.read_csv(CURRENT_DIRECTORY+f'\\weather\\renewable_generation_{date}.csv')
        weather_data=weather_data[weather_data["DateTime"]==f'{full_date}  {time}:00:00 {set}']
        weatherName=weather_data['GenNamepw']
        GenP=weather_data['MaxMW']
        dt=weather_data['DateTime']
        #print(dt)
        if weather==True:
            weather_gen(pw, GenP, weatherName)

        #while max(np.absolute(check))>1:
        #for t in range(0, 5):
        print("Sending:", BusKV, f"at hour X{hour}")

        federate.send(
                f"distribution_system_voltage", BusKV, "vector"
            )
        P=[]
        Q=[]
        federate.advance(advance)

        distribution_data_string = federate.recv(f"transmission_system_load")
        
        print(f"received data at time {hour} = {distribution_data_string}")

        
        if "," in distribution_data_string:
            distribution_data = ast.literal_eval(distribution_data_string)

        if not os.path.exists(opf_path):
            os.makedirs(opf_path)
        opf_file=opf_path + f"\\opf_load_data_X{hour}.csv"
        #pw.RunScriptCommand(f'SolvePrimalLP("{opf_file}")')

        #Tkv69, Dkv69=update_power(pw,P,Q, subID, opf_file)
        load_data = pw.GetParametersMultipleElement('load', ['BusNum', 'LoadID', 'LoadMW', 'LoadMVR'])
        PWMW = load_data['LoadMW']
        pw.RunScriptCommand(f'LogSave("{PARENT_DIRECTORY}\\Co-Simulation-Results\\{date}\\{percent}\\Weather_data_added\\log{hour}.txt")')
        #pw.SolvePowerFlow()
        #pw.RunScriptCommand(f'SolvePrimalLP("", "C:\\Users\\diwalli\\Houston-Co-Simulation-transportation-project\\transmission\\savelog.aux")')
        #pw.RunScriptCommand('SolvePowerFlow(RECTNEWT)')
        pw.RunScriptCommand(f'LogSave("{PARENT_DIRECTORY}\\Co-Simulation-Results\\{date}\\{percent}\\Weather_data_added\\log_after{hour}.txt")')

        #get_weather_buses()


        gen_data = pw.GetParametersMultipleElement('Gen', ['BusNum','AreaName','BusName','GenID','GenStatus','GenMW','GenMVR','GenMWMin','GenMWMax','GenMVRMin','GenMVRMax'])
       
        #pw.SolvePowerFlow()
        if weather==True:
            gen_path=PARENT_DIRECTORY + f"\\Co-Simulation-Results\\{date}\\{percent}\\Weather_data_added\\Generator_data"
        else:
            gen_path=PARENT_DIRECTORY + f"\\Co-Simulation-Results\\{date}\\{percent}\\Generator_data"
        if not os.path.exists(gen_path):
            os.makedirs(gen_path)
        gen_data.to_csv(gen_path + f"\\generator_data_hour_X{hour}.csv")


        
        
        #check=np.array(PWMW)-P
        #convergence=check_convergence(pw, Tkv69, Dkv69)
        TVoltage_data_check = pw.GetParametersMultipleElement('load', ['BusNum', 'BusKVVolt'])
        TVcheck = TVoltage_data_check['BusKVVolt']
        #convergence=check_convergence(pw, TVcheck,)
        #print(PWMW)
        #print(P)
            
            
    #pw.saveCase()
    
    
