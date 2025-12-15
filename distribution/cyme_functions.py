import cympy
import string
import locale
import os
import sys
import _db
import cympy.rm
import cympy.db
import cympy.study
import cympy.enums
import pandas as pd
# Location and name of .sxst file
CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))

#studyFolderPath = r'C:\Program Files\CYME\CYME\tutorial\How-to'
studyFolderPath = CURRENT_DIRECTORY


###############################################################################



#%% Open CYME Study and Verify that it loaded correctly

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


def load_database_create_study(database_name, studyFilePath):

    print('Opening CYME Database')
    print('')
    
    #cympy.db.ConnectDatabaseByName("United_Network_4_RemovingHeadNodes_testing")
    _db.ConnectDatabaseByName(database_name)
    
    locale.setlocale(locale.LC_NUMERIC, '')
    cympy.app.ActivateRefresh(True)
    
    #studyFilePath = studyFolderPath + studyFilename
    #cympy.study.Open(studyFilePath)
    #cympy.study.ActivateModifications(False)
    
    networks=_db.ListNetworks()
    #networks=networks[0:10]
    print(networks)
    
    
    
    print('Creating CYME Study')
    print('')
    
    cympy.study.New()
    cympy.study.LoadNetworks(networks)
    
    #locale.setlocale(locale.LC_NUMERIC, 'C:\\Program Files\\CYME\\CYME\\tutorial\\How-to')
    locale.setlocale(locale.LC_NUMERIC, '')
    # Deactivate the GUI refresh
    cympy.app.ActivateRefresh(False)
    
    
    cympy.study.Save(studyFilePath)
    cympy.study.Close()

    return

def open_study_file(studyFilePath):
    print('Opening CYME Study')
    print('')

    locale.setlocale(locale.LC_NUMERIC, '')
    #cympy.app.ActivateRefresh(True)
    cympy.app.ActivateRefresh(False)

    #cympy.db.ConnectDatabaseByName("United_Network_4_RemovingHeadNodes_testing")

    cympy.study.Open(studyFilePath)
    cympy.study.ActivateModifications(False)

def list_loads():
    
    #%% Open CYME Study and Verify that it loaded correctly

    # Run the Load Flow analysis
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()

    load_models=cympy.study.ListLoadModels()
    #print(load_models)
    
    spot_loads = cympy.study.ListDevices(cympy.enums.DeviceType.SpotLoad) 
    #spot_loads=spot_loads[0:5]
    distributed_loads = cympy.study.ListDevices(cympy.enums.DeviceType.DistributedLoad) 
    distributed_loads=distributed_loads[0:5]
    '''
    devices= cympy.study.ListDevices()
    for device in devices:
        gload=cympy.study.GetLoad(device.DeviceNumber, device.DeviceType)
        print(gload)
    '''
        
    #loads = cympy.study.ListDevices() 
    
    for load in spot_loads:
        #print("Spot Load")

        #load_id = load.GetValue("DeviceNumber")
        #load_info = cympy.study.QueryInfoDevice(KeywordID="EqState" , DeviceType=load.DeviceType, DeviceNumber=load.DeviceNumber)
        #print(load_info)
        load_id=load.DeviceNumber
        load_type=load.DeviceType
        load_loc=load.Location
        #load_loc=cympy.enums.DuctBankCoordinatesOrigin(load_id)
        load_section=load.SectionID
        #customers=load.ListCustomers()
        gload=cympy.study.GetDevice(load_id, cympy.enums.DeviceType.SpotLoad)
        
        #print(load.GetObjType())
        #print(gload.GetObjType())
        #gload.AddCustomerLoad("234567")
        #customers=cympy.study.Load.ListCustomers()
        #customers=gload.ListCustomers()
        #if gload != None:
        #print(load_id, load_type, load_loc, load_section)
        print(load_id)#, load_type, load_loc, load_section)
        #print(gload)
        #print(customers)
        #load_type = load.GetValue("DeviceType")
        #print(load_id, load_type, load_loc, load_section)
        load_kva_dist=cympy.study.QueryInfoDevice("DistKVAT", load_id, cympy.enums.DeviceType.SpotLoad) #total distributed load kva
        load_customers_total=cympy.study.QueryInfoDevice("TotalCons", load_id, cympy.enums.DeviceType.SpotLoad) #total load customers
        load_kw_spot=cympy.study.QueryInfoDevice("FSpotKWT", load_id, cympy.enums.DeviceType.SpotLoad) #fixed spot load kw
        load_kw_total=cympy.study.QueryInfoDevice("TotalKW", load_id, cympy.enums.DeviceType.SpotLoad) #total KW
        custnumber=cympy.study.QueryInfoDevice("CustNumber", load_id, cympy.enums.DeviceType.SpotLoad) #customer number
        custa=cympy.study.QueryInfoDevice("CustCKVAA", load_id, cympy.enums.DeviceType.SpotLoad) #customer connected to A
        #print("load_kw_spot", load_kw_spot, "total KW", load_kw_total, "Total Customers", load_customers_total, "Customer Number", custnumber, "CustomerA",custa)
        
    '''
    for load in distributed_loads:
        print("Distributed Load")
        load_id=load.DeviceNumber
        load_type=load.DeviceType
        load_loc=load.Location
        load_section=load.SectionID
        print(load_id, load_type, load_loc, load_section)
        load_kva_dist=cympy.study.QueryInfoDevice("DistKVAT", load_id, cympy.enums.DeviceType.DistributedLoad) #total distributed load kva
        load_customers_total=cympy.study.QueryInfoDevice("TotalCons", load_id, cympy.enums.DeviceType.DistributedLoad) #total load customers
        load_kw_spot=cympy.study.QueryInfoDevice("FSpotKWT", load_id, cympy.enums.DeviceType.DistributedLoad) #fixed spot load kw
        load_kw_total=cympy.study.QueryInfoDevice("TotalKW", load_id, cympy.enums.DeviceType.DistributedLoad) #total KW
        custnumber=cympy.study.QueryInfoDevice("CustNumber", load_id, cympy.enums.DeviceType.DistributedLoad) #customer number
        custa=cympy.study.QueryInfoDevice("CustCKVAA", load_id, cympy.enums.DeviceType.DistributedLoad) #customer connected to A
        print(load_kw_total,load_customers_total, "Customer Number", custnumber, "CustomerA",custa)
    '''

def create_new_load(load_name, load_id, load_loc):
    #NEED TO SAVE AFTER ADDING FOR IT TO TAKE EFFECT
    #THIS WORKS cympy.study.AddDevice adds load12345
    l1=cympy.study.AddDevice(load_name, cympy.enums.DeviceType.SpotLoad, load_id, "DEFAULT", load_loc, True)
    #l1.SetValue(15, "DemandA")
    return l1

def get_info_nodes():
    networks = cympy.study.ListNetworks()
    feeders = cympy.study.ListNetworks(cympy.enums.NetworkType.Feeder)
    networks=networks[0:1]
    load_flow = cympy.sim.LoadFlow()
    load_flow.Run()
    print(cympy.Describe("Node"))
    for network in networks:
        # Create empty lists for the worst low voltage, high voltage and total losses seen by the sources
        worst_low = []
        worst_high = []
        total_losses = []

        # Getting the low voltage sections on the network
        low_voltages = cympy.study.ListAbnormalConditions(cympy.enums.AbnormalConditionType.LowVoltage, network)
        # Getting the high voltage sections on the network
        high_voltages = cympy.study.ListAbnormalConditions(cympy.enums.AbnormalConditionType.HighVoltage, network)
        '''
        print(low_voltages)
        for l in low_voltages:
            print(l)
        print(high_voltages)
        for h in high_voltages:
            print(h)
        '''
        # Low voltage sections count on the network
        low_voltage_count = (len(low_voltages))
        # High voltage sections count on the network
        high_voltage_count = (len(high_voltages))

        # Getting the list of sources on the current network
        sources = cympy.study.ListNodes(cympy.enums.NodeType.SourceNode, network)
        nodes = cympy.study.ListNodes(cympy.enums.NodeType.Node, network)
        #print("ALL SYSTEM Sources")
        #print(sources)
        #print("ALL SYSTEM Nodes")
        #print(nodes)
        for node in nodes:
            node_id = node.ID
            nodex=node.X
            nodey=node.Y
            voltage_magnitude = cympy.study.QueryInfoNode('NodeRatedVoltage', node_id)
            kva_down = cympy.study.QueryInfoNode('CustKVAT', node_id)
            undervoltage = cympy.study.QueryInfoNode('DwLowVoltCount', node_id)
            print("voltage_magnitude", voltage_magnitude, "kva_down", kva_down)
            print("#undervoltage", undervoltage)
            #print(node_id, nodex, nodey)
            '''
            try:
                # Keywords are in the string format and must be converted to float for numerical values
                # Getting the worst low three phase voltage seen by source
                worst_low.append(locale.atof(cympy.study.QueryInfoNode('DwLowVoltWorst3PH', node_id)))
                # Getting the worst high three phase voltage seen by source
                worst_high.append(locale.atof(cympy.study.QueryInfoNode('DwHighVoltWorst3PH', node_id)))
                # Getting the total downstream kw losses
                total_losses.append(locale.atof(cympy.study.QueryInfoNode('DwKWLossTotal', node_id)))
            except ValueError as e:
                print("No value")  # Ignore source if no valid value if found
            '''  
        for source in sources:
            # Getting source node id
            source_id = source.ID
            source_x=source.X
            source_y=source.Y

            try:
                # Keywords are in the string format and must be converted to float for numerical values
                # Getting the worst low three phase voltage seen by source
                worst_low.append(locale.atof(cympy.study.QueryInfoNode('DwLowVoltWorst3PH', source_id)))
                # Getting the worst high three phase voltage seen by source
                worst_high.append(locale.atof(cympy.study.QueryInfoNode('DwHighVoltWorst3PH', source_id)))
                # Getting the total downstream kw losses
                total_losses.append(locale.atof(cympy.study.QueryInfoNode('DwKWLossTotal', source_id)))
            except ValueError as e:
                print("No value")  # Ignore source if no valid value if found

def get_node_info(node_name):
    node_info = cympy.study.QueryInfoDevice(
    element_type="Node", 
    device_id=node_name, 
    phases="ABC"  # Specify the phases you want to query
    )
    
    if node_info:
    # The QueryInfoDevice method returns a dictionary of results.
    # The voltage result can be accessed by a specific key.
    # Common keys include 'Voltage(L-G) (kV)' for line-to-ground voltage.
    # You may need to inspect the 'node_info' object to find the exact key.
    
    # Example: Accessing voltage magnitude for phase A
        try:
            voltage_a = node_info.get('Voltage(L-G) (kV) A')
            print(f"Voltage at node '{node_name}' (Phase A): {voltage_a} kV")
        except KeyError:
            print("Voltage data not found for the specified node and phase.")
    else:
        print(f"Node '{node_name}' not found or no results available.")
    return

def find_loads_at_bus(target_bus_name):

    # 2. Find the bus device by its name.
    bus_object = None
    for bus in cympy.study.GetDevices(cympy.enums.DeviceType.Bus):
        if bus.Name == target_bus_name:
            bus_object = bus
            break
    
    if not bus_object:
        print(f"Bus '{target_bus_name}' not found.")
    else:
        # 3. Retrieve all devices connected to the target bus.
        # The 'AttachedDevices' property provides a list of all equipment connected to the bus.
        attached_devices = bus_object.AttachedDevices
        
        found_loads = []
        for device in attached_devices:
            if device.DeviceType == cympy.enums.DeviceType.Load:
                # 4. Get the full object for each load and extract its properties.
                load_object = cympy.db.GetDevice(device.DeviceId)
                found_loads.append(load_object)
    
        if not found_loads:
            print(f"No loads found at bus '{target_bus_name}'.")
        else:
            # 5. Loop through the found loads and display their data.
            for i, load in enumerate(found_loads):
                print(f"--- Load {i+1} at Bus '{target_bus_name}' ---")
                
                # Use `GetProperty()` to retrieve specific attributes.
                # Example: Get the nominal value for the load.
                nominal_kw = load.GetProperty("NominalValue.KW")
                nominal_kvar = load.GetProperty("NominalValue.KVAR")
                nominal_kva = load.GetProperty("NominalValue.KVA")
                
                print(f"Nominal Load (kW): {nominal_kw}")
                print(f"Nominal Load (kvar): {nominal_kvar}")
                print(f"Nominal Load (kVA): {nominal_kva}")
    return

def get_node_kW_Totals():
    kw_totals=pd.DataFrame(columns=["Node", "Load ID", "kW Total"])
    networks = cympy.study.ListNetworks()
    #for network in networks:
    nodes =cympy.study.ListDevices(cympy.enums.DeviceType.SpotLoad) 
    for node in nodes:
        #print(node.Location)
        load_id=node.DeviceNumber
        #print("Spot Location ", cympy.study.QueryInfoDevice("SpotLocat", load_id, cympy.enums.DeviceType.SpotLoad)) #total KW            
        load_kw_total=cympy.study.QueryInfoDevice("TotalKW", load_id, cympy.enums.DeviceType.SpotLoad) #total KW            
        nodeid=cympy.study.QueryInfoDevice("SpotLocat", load_id, cympy.enums.DeviceType.SpotLoad)
        kw_totals = pd.concat([pd.DataFrame([[load_id, load_id, load_kw_total]], columns=kw_totals.columns), kw_totals], ignore_index=True)            
    
    
        node_real=get_node_object(load_id)
        print(node_real)
    
    return kw_totals

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
            print(load_kw_total)
    return load_totals

def report_overloads_by_network(network_file, feeder_file):
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
    
    return

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
    #summary_report_full = summary_report_full[(summary_report_full > 0).any(axis=1)]
    summary_report_full.to_csv(output_file_path)
    
    return

if __name__ == "__main__":
    database_name="Bluebonnet_July24th_wtoSubstation_testing"
    studyFolderPath = CURRENT_DIRECTORY
    studyFilename = r'\testing_cyme_fullbonnet_file_10_net.xst'
    
    studyFilePath = studyFolderPath + studyFilename
    
    #load_database_create_study(database_name, studyFilePath)
    #studyFilename = r'\testing_cyme_fullbonnet.xst'

    open_study_file(studyFilePath)
    #list_loads()
    output_file=studyFolderPath + "\\test_overload_summary.csv"
    output_file2=studyFolderPath + "\\test_overload_summary_full.csv"
    output_file_all=studyFolderPath + "\\test_overloads_all.csv"

    #report_overloads_by_network(output_file, output_file2)
    report_all_overloads(output_file_all)
    #kw = get_node_load_Totals()
    #output_file=studyFolderPath + "\\test_summary.csv"
    #summary_for_network(output_file)
    #total=get_node_kW_Totals()
    #print(total)
    '''
    networks = cympy.study.ListNetworks()
    all_devices=cympy.study.ListDevices()
    for device in all_devices:
        find_loads_at_bus(device.DeviceNumber)
    '''
    #custnum=cympy.study.FindDeviceInfo("DeviceNumber", networks)
    #print(custnum)
    