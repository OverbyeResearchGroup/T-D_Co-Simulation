# -*- coding: utf-8 -*-
import os
import csv
import sys
#from esa import SAW
import numpy as np
#from csv_reader import csv_reader
import pandas as pd
from pandas import DataFrame
import dss as dss_py
import time
import ast

import cympy
import string
import locale
import _db
import cympy.rm
import cympy.db
import cympy.study
import cympy.enums

start_time = time.time()


# Hack to add helics_utils to path
# TODO: use setup.py instead
CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))
sys.path.append(os.path.join(CURRENT_DIRECTORY, ".."))

from helics_utils import Federate, setup_helics_federate
import opendssdirect as odd



CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))
PARENT_DIRECTORY = os.path.realpath(os.path.dirname(CURRENT_DIRECTORY))
# TRANSPORTATION_DIRECTORY="C:\\Users\\diwalli\\PycharmProjects\\transportation"

'''
Latitude = subs.Latitude
Longitude = subs.Longitude

Lpercent = 30 / 100
Hpercent = 20 / 100
'''
system = "EV"

weather = False
date = 'May 3'
# start=6912
duration = 25

weather_file=""

if system.lower()=="base":
    percent='Base'
else:

    #percent = f"{int(Lpercent * 100)}% Light {int(Hpercent * 100)}% Heavy"
    evfile = os.environ["EVfilepath"]
    percent_string = evfile.split(".")
    percent = percent_string[0]
    percent=percent.split("\\")
    percent=percent[-1]

if date == 'Oct 16':
    start = 6912
elif date == "Feb 14":
    start = 1068
elif date == "Aug. 6":
    start = 5208
    #start = 5233
else:
    start = 2928


Powers = []
# percent=f"{Lpercent*100}_Light_{Hpercent*100}_Heavy"
# percent="Base"

power_csv = pd.DataFrame()

# power_csv["Hour"]=np.arange(0, 24, 1)

all_buses_power = []
all_buses_voltage = []
all_buses_voltagepu = []
all_transformers = []
all_transformer_names = []
Violations = []
Violations2 = []

#EV_loads = pd.read_csv(evfile)
#print(evfile)

def open_study_file(studyFilePath):
    print('Opening CYME Study')
    print('')

    locale.setlocale(locale.LC_NUMERIC, '')
    #cympy.app.ActivateRefresh(True)
    cympy.app.ActivateRefresh(False)

    #cympy.db.ConnectDatabaseByName("United_Network_4_RemovingHeadNodes_testing")

    cympy.study.Open(studyFilePath)
    cympy.study.ActivateModifications(False)
    #print(DSS_DIRECTORY)
    


def initialize_study():
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()


def get_node_object(node_find):
    networks = cympy.study.ListNetworks()
    for network in networks:
        nodes = cympy.study.ListNodes(cympy.enums.NodeType.Node, network)
        for node in nodes:
            node_id = node.ID
            if node_id==node_find:
                return node
            else:
                return None
            
def get_node_load_Totals():
    load_totals=pd.DataFrame(columns=["Node ID", "kW Total", "kvar Total"])
    networks = cympy.study.ListNetworks()
    for network in networks:
        nodes = cympy.study.ListNodes(cympy.enums.NodeType.Node, network)
        for node in nodes:
            load_kw_total=cympy.study.QueryInfoDevice("TotalKW", node.ID, cympy.enums.DeviceType.SpotLoad) #total KW            
            load_kvar_total=cympy.study.QueryInfoDevice("TotalKVAR", node.ID, cympy.enums.DeviceType.SpotLoad) #total KW            
            load_totals = pd.concat([pd.DataFrame([[node.ID, load_kw_total, load_kvar_total]], columns=load_totals.columns), load_totals], ignore_index=True)            

            with open("test.txt", 'a') as file:
                file.write(f"{load_kvar_total}\n")
    return load_totals
    
def get_load_Totals():
    load_totals=pd.DataFrame(columns=["Device ID", "kW Total", "kvar Total"])
    
    nodes =cympy.study.ListDevices(cympy.enums.DeviceType.SpotLoad) 
    for node in nodes:
        id_num=node.DeviceNumber
        load_kw_total=cympy.study.QueryInfoDevice("TotalKW", id_num, cympy.enums.DeviceType.SpotLoad) #total KW            
        load_kvar_total=cympy.study.QueryInfoDevice("TotalKVAR", id_num, cympy.enums.DeviceType.SpotLoad) #total KW            
        load_totals = pd.concat([pd.DataFrame([[id_num, load_kw_total, load_kvar_total]], columns=load_totals.columns), load_totals], ignore_index=True)            
    return load_totals

def update_load(nodes, load_df, hour):
    list_loads=cympy.study.ListDevices(cympy.enums.DeviceType.SpotLoad) 
    for nid, load in zip(load_df["Node ID"], load_df[ f"{hour}"]):
        for load_object in list_loads:
            if nid==load_object.DeviceNumber:
                load_id= load_object.DeviceNumber
                load_loc=load.Location
                #NEED TO SAVE AFTER ADDING FOR IT TO TAKE EFFECT
                #THIS WORKS cympy.study.AddDevice adds load12345
                l1=cympy.study.AddDevice(f"Load_{load_id}", cympy.enums.DeviceType.SpotLoad, load_id, "DEFAULT", load_loc, True)
                l1.SetValue(load, "DemandA")
        return 


def summary_for_network(output_file):

    locale.setlocale(locale.LC_NUMERIC, '')
    
    # Deactivate the GUI refresh
    cympy.app.ActivateRefresh(False)
    
    # Run the Load Flow analysis
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()
    
    # Get the list of networks
    networks = cympy.study.ListNetworks()
    
    # Create an empty list for the lines to show in the report
    lines = []
    
    # Iterating through all networks
    for network in networks:
        # Create empty lists for the worst low voltage, high voltage and total losses seen by the sources
        worst_low = []
        worst_high = []
        total_losses = []
    
        # Getting the low voltage sections on the network
        low_voltages = cympy.study.ListAbnormalConditions(cympy.enums.AbnormalConditionType.LowVoltage, network)
        # Getting the high voltage sections on the network
        high_voltages = cympy.study.ListAbnormalConditions(cympy.enums.AbnormalConditionType.HighVoltage, network)
    
        # Low voltage sections count on the network
        low_voltage_count = (len(low_voltages))
        # High voltage sections count on the network
        high_voltage_count = (len(high_voltages))
    
        # Getting the list of sources on the current network
        sources = cympy.study.ListNodes(cympy.enums.NodeType.SourceNode, network)
        for source in sources:
            # Getting source node id
            source_id = source.ID
    
            try:
                # Keywords are in the string format and must be converted to float for numerical values
                # Getting the worst low three phase voltage seen by source
                worst_low.append(locale.atof(cympy.study.QueryInfoNode('DwLowVoltWorst3PH', source_id)))
                # Getting the worst high three phase voltage seen by source
                worst_high.append(locale.atof(cympy.study.QueryInfoNode('DwHighVoltWorst3PH', source_id)))
                # Getting the total downstream kw losses
                total_losses.append(locale.atof(cympy.study.QueryInfoNode('DwKWLossTotal', source_id)))
            except ValueError as e:
                pass  # Ignore source if no valid value if found
    
        try:
            # Get the worst case
            worst_low = min(worst_low)
            worst_high = max(worst_high)
            total_losses = max(total_losses)
    
        # Catch a thrown exception
        except cympy.err.CymError as e:
            print(e.GetMessage())
            worst_low = 0.0
            worst_high = 0.0
            total_losses = 0.0
            low_voltage_count = 0
            high_voltage_count = 0
    
        # Appending data to lines
        lines.append([network, worst_low, worst_high, low_voltage_count, high_voltage_count, total_losses])
    
    # Execute Short Circuit analysis
    try:
        sc = cympy.sim.ShortCircuit()
        # Set the method to summary short-circuit in phase
        sc.SetValue('SC', 'ParametersConfigurations[0].Domain')
        sc.Run()
    except cympy.err.CymError as e:
        print(e.GetMessage())
    
    # Iterating through the existing lines of the report
    for line in lines:
        # Getting network id of the data in the line
        network_id = line[0]
    
        # Create an empty list for the maximum and minimum faults
        min_LLL = []
        max_LLL = []
        min_LG = []
        max_LG = []
    
        # Getting list of nodes of the current network
        nodes = cympy.study.ListNodes(cympy.enums.NodeType.All, network_id)
        for node in nodes:
            # Getting node id
            node_id = node.ID
    
            try:
                # Getting min LLL fault
                LLL_min = locale.atof(cympy.study.QueryInfoNode('LLLampKmin', node_id))
                if LLL_min != 0.0:
                    min_LLL.append(LLL_min)
    
                # Getting max LLL fault
                LLL_max = locale.atof(cympy.study.QueryInfoNode('LLLampKmax', node_id))
                if LLL_max != 0.0:
                    max_LLL.append(LLL_max)
    
                LG_min = locale.atof(cympy.study.QueryInfoNode('LGampKmin', node_id))
                if LG_min != 0.0:
                    min_LG.append(LG_min)
    
                LG_max = locale.atof(cympy.study.QueryInfoNode('LGampKmax', node_id))
                if LG_max != 0.0:
                    max_LG.append(LG_max)
            except ValueError as e:
                pass
    
        try:
            # Get minimal LLL fault
            min_LLL = min(min_LLL)
            # Get maximal LLL fault
            max_LLL = max(max_LLL)
            min_LG = min(min_LG)
            max_LG = max(max_LG)
        except cympy.err.CymError as e:
            print(e.GetMessage())
            min_LLL = 0.0
            max_LLL = 0.0
            min_LG = 0.0
            max_LG = 0.0
        # Appending data to line
        line.append(min_LLL)
        line.append(max_LLL)
        line.append(min_LG)
        line.append(max_LG)
    
    # Report generation
    # Create the report and the name of the columns
    report = cympy.rm.CustomReport('SummaryReport', ['NetworkID', 'Worst Under\n Voltage (%)', 'Worst Over\n Voltage (%)',
                                                     'Number of\n Under Voltages', 'Number of\n High Voltages', 'Total\n Losses (kW)',
                                                     'Minimum\n LLL Fault (A)', 'Maximum\n LLL Fault (A)', 'Minimum\n LG Fault (A)', 'Maximum\n LG Fault (A)'])
    for line in lines:
        # Create a list with the elements of the report line
        cells = []
        # Creating a hyperlink network cell
        c_network = cympy.rm.NetworkCell(line[0])
        cells.append(c_network)
    
        # Adding the other values to the report
        c_others = line[1:3]
        for cell in c_others:
            cells.append(cympy.rm.FloatCell(round(cell, 2)))
    
        c_others = line[3:5]
        for cell in c_others:
            cells.append(cympy.rm.IntCell(cell))
    
        c_others = line[5:]
        for cell in c_others:
            cells.append(cympy.rm.FloatCell(round(cell, 2)))
    
        # Adding the row to the report
        report.AddRow(cells)
    
    try:
        report.Save(cympy.enums.ReportModeType.CSV, output_file)
    
    except cympy.err.CymError as e:
        print(e.GetMessage())
        # If the report cannot show, print all the values to find the problem
        print('NetworkID'.rjust(20, ' ')),
        print('Worst Under Voltage'.rjust(20, ' ')),
        print('Worst Over Voltage'.rjust(20, ' ')),
        print('Number of Under Voltages'.rjust(20, ' ')),
        print('Number of High Voltages'.rjust(20, ' ')),
        print('Total Losses'.rjust(20, ' ')),
        print('Minimum Fault'.rjust(20, ' ')),
        print('Maximum Fault'.rjust(20, ' '))
    
        for line in lines:
            for s in line:
                print(str(s).rjust(20, ' '))
            print('\n')
    finally:
        cympy.app.ActivateRefresh(True)
    return

def report_overloads_by_network(output_file):
    '''
    DwOverloadCondWorstA
    DwOverloadCondWorstB
    DwOverloadCondWorstC
    DwOverloadCondWorstN
    DwOverloadCount
    DwOverloadCountA
    DwOverloadCountB
    DwOverloadCountC
    DwOverloadCountN
    '''
    locale.setlocale(locale.LC_NUMERIC, '')
    
    # Deactivate the GUI refresh
    cympy.app.ActivateRefresh(False)
    
    # Run the Load Flow analysis
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()
    
    # Get the list of networks
    networks = cympy.study.ListNetworks()
    print(networks)
    # Create an empty list for the lines to show in the report
    lines = []
    
    summary_report=pd.DataFrame(columns=['Network', 'Worst Overload A', 'Worst Overload B', 'Worst Overload C',
                                                     'Worst Overload N', 'Number of Overloads A', 'Number of Overloads B',
                                                     'Number of Overloads C', 'Number of Overloads N'])
    
    #all_overloads_report=pd.DataFrame(columns=['Network',"Node", "Overload A", " Overload B",  "Overload C", "Overload N"])
    # Iterating through all networks
    for network in networks:
        # Create empty lists for the worst low voltage, high voltage and total losses seen by the sources
        OverloadsA = []
        OverloadsB = []
        OverloadsC = []
        OverloadsN=[]
        overload_countA=0
        overload_countB=0
        overload_countC=0
        overload_countN=0
        sources = cympy.study.ListNodes(cympy.enums.NodeType.SourceNode, network)
        for source in sources:
            # Getting source node id
            source_id = source.ID        
            try:
                # Keywords are in the string format and must be converted to float for numerical values
                OverloadsA.append(locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstA', source_id)))
                OverloadsB.append(locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstB', source_id)))
                OverloadsC.append(locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstC', source_id)))
                OverloadsN.append(locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstN', source_id)))
                overload_countA =int(overload_countA + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountA', source_id)))
                overload_countB =int(overload_countB + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountB', source_id)))
                overload_countC = int(overload_countC + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountC', source_id)))
                overload_countN = int(overload_countN + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountN', source_id)))
            except ValueError as e:
                pass  # Ignore source if no valid value if found
    
        try:
            # Get the worst case
            worst_A = min(OverloadsA)
            worst_B = max(OverloadsB)
            worst_C = max(OverloadsC)
            worst_N = max(OverloadsN)
    
        # Catch a thrown exception
        except cympy.err.CymError as e:
            print(e.GetMessage())
            worst_A = 0.0
            worst_B = 0.0
            worst_C = 0.0
            worst_N = 0.0
            overload_countA=0
            overload_countB=0
            overload_countC=0
            overload_countN=0
    
        # Appending data to lines
        
        df = pd.DataFrame([[network, worst_A, worst_B, worst_C,worst_N, overload_countA, overload_countB, overload_countC, overload_countN]], 
                          columns=['Network', 'Worst Overload A', 'Worst Overload B', 'Worst Overload C',
                                                                           'Worst Overload N', 'Number of Overloads A', 'Number of Overloads B',
                                                                           'Number of Overloads C', 'Number of Overloads N'])
        summary_report = pd.concat([summary_report, df])
        #lines.append([network, worst_A, worst_B, worst_C, overload_countA, overload_countB, overload_countC])
    
    summary_report.to_csv(output_file, index=False)
    
    return
   
def report_overloads_by_network_and_source(network_file, feeder_file):
    '''
    DwOverloadCondWorstA
    DwOverloadCondWorstB
    DwOverloadCondWorstC
    DwOverloadCondWorstN
    DwOverloadCount
    DwOverloadCountA
    DwOverloadCountB
    DwOverloadCountC
    DwOverloadCountN
    '''
    locale.setlocale(locale.LC_NUMERIC, '')
    
    # Deactivate the GUI refresh
    cympy.app.ActivateRefresh(False)
    
    # Run the Load Flow analysis
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()
    
    # Get the list of networks
    networks = cympy.study.ListNetworks()
    #print(networks)
    # Create an empty list for the lines to show in the report
    lines = []
    
    summary_report=pd.DataFrame(columns=['Network', 'Worst Overload A', 'Worst Overload B', 'Worst Overload C',
                                                     'Worst Overload N', 'Number of Overloads A', 'Number of Overloads B',
                                                     'Number of Overloads C', 'Number of Overloads N'])
    
    summary_report_full=pd.DataFrame(columns=['Network', 'SourceNode','Worst Overload A', 'Worst Overload B', 'Worst Overload C',
                                                     'Worst Overload N', 'Number of Overloads A', 'Number of Overloads B',
                                                     'Number of Overloads C', 'Number of Overloads N'])
    #all_overloads_report=pd.DataFrame(columns=['Network',"Node", "Overload A", " Overload B",  "Overload C", "Overload N"])
    # Iterating through all networks
    for network in networks:
        # Create empty lists for the worst low voltage, high voltage and total losses seen by the sources
        OverloadsA = []
        OverloadsB = []
        OverloadsC = []
        OverloadsN=[]
        overload_countA=0
        overload_countB=0
        overload_countC=0
        overload_countN=0
        sources = cympy.study.ListNodes(cympy.enums.NodeType.SourceNode, network)
        for source in sources:
            # Getting source node id
            source_id = source.ID        
            try:
                # Keywords are in the string format and must be converted to float for numerical values
                worst_A = locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstA', source_id))
                worst_B = locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstB', source_id))
                worst_C = locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstC', source_id))
                worst_N = locale.atof(cympy.study.QueryInfoNode('DwOverloadCondWorstN', source_id))
                OverloadsA.append(worst_A)
                OverloadsB.append(worst_B)
                OverloadsC.append(worst_C)
                OverloadsN.append(worst_N)
                overload_countA =int(overload_countA + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountA', source_id)))
                overload_countB =int(overload_countB + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountB', source_id)))
                overload_countC = int(overload_countC + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountC', source_id)))
                overload_countN = int(overload_countN + locale.atof(cympy.study.QueryInfoNode('DwOverloadCountN', source_id)))
                
                df_full = pd.DataFrame([[network, source_id, worst_A, worst_B, worst_C,worst_N, locale.atof(cympy.study.QueryInfoNode('DwOverloadCountA', source_id)), 
                                         locale.atof(cympy.study.QueryInfoNode('DwOverloadCountB', source_id)), locale.atof(cympy.study.QueryInfoNode('DwOverloadCountC', source_id)), 
                                         locale.atof(cympy.study.QueryInfoNode('DwOverloadCountN', source_id))]], 
                                  columns=['Network', 'SourceNode','Worst Overload A', 'Worst Overload B', 'Worst Overload C',
                                                                                   'Worst Overload N', 'Number of Overloads A', 'Number of Overloads B',
                                                                                   'Number of Overloads C', 'Number of Overloads N'])
                summary_report_full = pd.concat([summary_report_full, df_full])
        
            except ValueError as e:
                pass  # Ignore source if no valid value if found
    
        try:
            # Get the worst case
            worst_A = min(OverloadsA)
            worst_B = max(OverloadsB)
            worst_C = max(OverloadsC)
            worst_N = max(OverloadsN)
    
        # Catch a thrown exception
        except cympy.err.CymError as e:
            print(e.GetMessage())
            worst_A = 0.0
            worst_B = 0.0
            worst_C = 0.0
            worst_N = 0.0
            overload_countA=0
            overload_countB=0
            overload_countC=0
            overload_countN=0
            
            
        # Appending data to lines
        
        df = pd.DataFrame([[network, worst_A, worst_B, worst_C,worst_N, overload_countA, overload_countB, overload_countC, overload_countN]], 
                          columns=['Network', 'Worst Overload A', 'Worst Overload B', 'Worst Overload C',
                                                                           'Worst Overload N', 'Number of Overloads A', 'Number of Overloads B',
                                                                           'Number of Overloads C', 'Number of Overloads N'])
        summary_report = pd.concat([summary_report, df])
        #lines.append([network, worst_A, worst_B, worst_C, overload_countA, overload_countB, overload_countC])
    
    summary_report.to_csv(network_file, index=False)
    summary_report_full.to_csv(feeder_file, index=False)

def report_all_overloads(output_file_path):
    '''
    DwOverloadCondWorstA
    DwOverloadCondWorstB
    DwOverloadCondWorstC
    DwOverloadCondWorstN
    DwOverloadCount
    DwOverloadCountA
    DwOverloadCountB
    DwOverloadCountC
    DwOverloadCountN
    '''
    locale.setlocale(locale.LC_NUMERIC, '')
    
    # Deactivate the GUI refresh
    cympy.app.ActivateRefresh(False)
    
    # Run the Load Flow analysis
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()
    
    # Get the list of networks
    networks = cympy.study.ListNetworks()
    #print(networks)
    # Create an empty list for the lines to show in the report
    lines = []
    
   
    summary_report_full=pd.DataFrame(columns=['Network', 'Overhead Line','Overload % A', 'Overload % B', 'Overload % C',
                                                     'Overload % N'])
    #all_overloads_report=pd.DataFrame(columns=['Network',"Node", "Overload A", " Overload B",  "Overload C", "Overload N"])
    # Iterating through all networks
    for network in networks:
        # Create empty lists for the worst low voltage, high voltage and total losses seen by the sources
        
        #sources = cympy.study.ListDevices(cympy.enums.DeviceType.OverheadLineUnbalanced)
        sources = cympy.study.ListDevices(cympy.enums.DeviceType.OverheadByPhase)
        for source in sources:
            # Getting source node id
            #print(source.DeviceType)
            try:
                # Keywords are in the string format and must be converted to float for numerical values
                source_id = source.DeviceNumber        
                overloadampsA = locale.atof(cympy.study.QueryInfoDevice('OverloadAmpsA', source_id, source.DeviceType))
                overloadampsB = locale.atof(cympy.study.QueryInfoDevice('OverloadAmpsB', source_id, source.DeviceType))
                overloadampsC = locale.atof(cympy.study.QueryInfoDevice('OverloadAmpsC', source_id, source.DeviceType))
                overloadampsN = locale.atof(cympy.study.QueryInfoDevice('OverloadAmpsN', source_id, source.DeviceType))
                #print(source_id, source.DeviceType)
                
                df = pd.DataFrame([[network, source_id, overloadampsA, overloadampsB, overloadampsC,overloadampsN]], 
                                  columns=['Network', 'Overhead Line', 'Overload % A', 'Overload % B', 'Overload % C',
                                                                                   'Overload % N'])
                summary_report_full = pd.concat([summary_report_full, df])
                
            except ValueError as e:
                pass  # Ignore source if no valid value if found
    

    
      
      
        #lines.append([network, worst_A, worst_B, worst_C, overload_countA, overload_countB, overload_countC])
    summary_report_full = summary_report_full.set_index(['Network', 'Overhead Line']) 
    summary_report_full = summary_report_full[(summary_report_full > 0).any(axis=1)]
    summary_report_full.to_csv(output_file_path)
    
    return


    
    return    

if __name__ == "__main__":
    load_data=pd.read_csv(CURRENT_DIRECTORY + "\\load_data_dummy_data.csv")
    #set wait times here based on station name
    database_name="Bluebonnet_July24th_wtoSubstation_testing"
    studyFolderPath = CURRENT_DIRECTORY
    studyFilename = r'\testing_cyme_fullbonnet_file_10_net.xst'
    
    studyFilePath = studyFolderPath + studyFilename
    
    open_study_file(studyFilePath)
    initialize_study()

    #del subs

   
    federate = setup_helics_federate(
        federate_name=f"distribution_system",
        subscriptions=[f"distribution_system_voltage"],
        publications=[
            (f"transmission_system_load", "vector")
        ],

    )
    # print(f"transmission_system_{bus}_{station}_substation_load", "vector")
    # print(f"Working on bus {bus}")
    # Ov_loads = pd.read_csv(os.path.join(CURRENT_DIRECTORY,"overloads_EV.csv"))
    # Ov_loads=DataFrame()
    # all_subs = []
    h = []
    h.append('X1')
    for i in range(1, duration):
        h.append(f'X{i}')

    power_csv = pd.DataFrame()
    transformer_csv = pd.DataFrame()
    voltage_csv = pd.DataFrame()

    networks = cympy.study.ListNetworks()
    nodes=[]
    for network in networks:
        node_network = cympy.study.ListNodes(cympy.enums.NodeType.Node, network)
        nodes=nodes + node_network

    #transformer_csv = pd.DataFrame(columns=feeders)
    #voltage_csv = pd.DataFrame(columns=feeders)
    #power_csv = pd.DataFrame(columns=feeders)

    hour_count_t = []
    #hour_count_t.append(start)
    for i in range(0, duration-1):
        hour_count_t.append(start + i)
    multiplier=1
    #EV_hold_over=0
    hour = 0
    EV_loads = pd.read_csv(evfile)
    #time.sleep(sp + 1956)
    prev_voltage = 0
    hour_count = []
    #hour_count.append(1)
    #hour_count_t.append(1)
    hour_0 = 0
    for i in range(1, duration):
        hour_count.append(hour_0 + i)
    print(hour_count)
    index_counter=1
    advance=0
    do_over=0
    #advance = advance + 1
    #federate.advance(advance)
    count_runs=0
    #EV_loads["Hold"]=0
    EV_busloads = EV_loads
    federate.advance(advance)


    for t, hour in zip(hour_count_t, hour_count):
        count_runs=count_runs+1

        Voltages = []
        Transformers = []
        Powers_save = []
        Ov_loads = DataFrame()
        all_subs = []

        advance = advance+1
       

        EV_nodes=EV_busloads["Node Name"].tolist()
        # setup_opendss_simulator(Area, station)
        EV_sum_b = EV_busloads[f"X{hour}"].sum()*1000*multiplier
        EV_sum=EV_sum_b#+EV_hold_over_sum
        print("EV SUM FOR SUBSTATION", EV_sum_b)#*1000)
        #EV_hold_over=EV_sum_b*1000-EV_sum
        print(multiplier)#, EV_hold_over_sum)
        print("EV SUM FOR SUBSTATION+hold", EV_sum)#*1000)
        # odd.Circuit.SetActiveBus(station)
        #load_data= pd.read_csv(load_data_file)

        #odd.Text.Command(f"Solve mode=snapshot")
        load_flow = cympy.sim.LoadFlow()
        load_flow.Run()

        


        load = load_data[["Node ID", f"{hour}"]] #+ EV_sum# * 1000
        #print("Max timeseries:", loads.max())

        #print("LOAD FOR SUBSTATION from timeseries:", load)

        #odd.dss_lib.Loads_Set_kW(loads)

        #print("CHECK IF TIMESERIES CHANGED CORRECTLY:", odd.dss_lib.Loads_Get_kW())



        # while check>1:
        # for t in range(0, 5):
        #load_scale = load_scaling_factor[t]  # + EV * 1000
 
        

        # print(f"Solving at time t = {t + 1}")
        load_flow.Run()
        
        load_totals=get_load_Totals()
        
        load_totals.to_csv("test.csv")
        
        id_list=load_totals["Device ID"].values
        kw_totals=load_totals["kW Total"].values
        kvar_totals=load_totals["kvar Total"].values


        #send_power= list(zip(id_list, kw_totals, kvar_totals))
        kw_totals = [int(item) for item in kw_totals]
        send_power=kw_totals#[0:4]
        #send_power=[advance, hour]
        DIRECTORY = PARENT_DIRECTORY
        dss = os.path.join(DIRECTORY,
                           f"Co-Simulation-Results\\{date}\\{percent}{weather_file}\\Overloads_{system}\\X{hour}")
        dssmis = os.path.join(DIRECTORY, f"Co-Simulation-Results\\{date}\\{percent}{weather_file}\\Summary\\X{hour}")

        dssv = os.path.join(DIRECTORY,
                            f"Co-Simulation-Results\\{date}\\{percent}{weather_file}\\Voltages\\X{hour}")


        #print(send_power)
        # odd.run_command('Solve')
        
        print("advance is", advance)

        print("Sending:", send_power, f"at hour X{hour}")
        federate.send(
            f"transmission_system_load", send_power, "vector"
        )
        
        print("advance is", advance)
        federate.advance(advance)


        transmission_data_string = federate.recv(
            f"distribution_system_voltage"
        )


        #print(transmission_data_string)



        print(f"received voltage at time {hour} = {transmission_data_string}")
        #time.sleep(sp+20)



        # print("Voltage Received", float(voltage))
        # print("Voltage Negative?", float(voltage)<0)
        count = 0
        

        update_load(nodes, load, hour)
        # print(f"Solving at time t = {t + 1}")
        load_flow.Run()
        #f_total_load = odd.Circuit.TotalPower()
        #f_totals.append(abs(f_total_load[0]))
        # print(f"all load names {f}")
        # print(odd.Loads.AllNames())
        names = odd.Loads.AllNames()


      
       
    if "," in transmission_data_string:
        transmission_data = ast.literal_eval(transmission_data_string)

        # assert odd.Vsources.First() == 1
        
        #odd.dss_lib.Vsources_Set_BasekV(float(voltage))
        '''
        for node_in, voltage, multiplier, rerun in transmission_data:
            for node in nodes:
                if node_in == node.ID:
                    None
                    #cympy.study.SetValueNode(voltage, , node.ID)
        '''

        summary_folder= PARENT_DIRECTORY + f"\\Co-Simulation-Results\\{date}\\Summary\\"
        if not summary_folder:
            os.makedirs(summary_folder)
        '''   
        summary_file=summary_folder + f"summary_X{hour}.csv"
        summary_for_network(summary_file)
        
        
        overload_summary_folder= PARENT_DIRECTORY + f"\\Co-Simulation-Results\\{date}\\Overload Summary\\"
        if not overload_summary_folder:
            os.makedirs(overload_summary_folder)
        '''
        all_overloads_folder= PARENT_DIRECTORY + f"\\Co-Simulation-Results\\{date}\\Overloads\\"
        if not all_overloads_folder:
            os.makedirs(all_overloads_folder)
            
        overload_file_network=overload_summary_folder + f"overload_summary_by_network_X{hour}.csv"
        overload_file_source=overload_summary_folder + f"overload_summary_by_source_X{hour}.csv"
        report_overloads_by_network_and_source(overload_file_network,overload_file_source)
        
        all_overloads_file = all_overloads_folder+f"all_overloads_X{hour}.csv"
        report_all_overloads(all_overloads_file)
   
    index_counter=index_counter+1
    #time.sleep(470)





    print("Loop ran", count_runs, "times")

    # Ov_loads.to_csv(PARENT_DIRECTORY + f"\\Co-Simulation-Co-Simulation-Results\\{date}\\Overloads\\{station}_Overloads_EV.csv")

    


    print("My program took", (time.time() - start_time) / 3600, "to run")
