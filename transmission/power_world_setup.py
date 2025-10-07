from saw_editing_file import SAW
import numpy as np
import os, sys
import csv
import pandas as pd
from csv import reader
import ast

CURRENT_DIRECTORY = os.path.realpath(os.path.dirname(__file__))
PARENT_DIRECTORY = os.path.realpath(os.path.dirname(CURRENT_DIRECTORY))
sys.path.append(os.path.join(CURRENT_DIRECTORY, ".."))


def setup_voltage_data(pw, subID):
    # pw.SolvePowerFlow()
    IDs = pd.DataFrame()
    IDs["SubNum"] = subID
    Bus_data = pw.GetParametersMultipleElement('load', ['SubNum', 'BusNum', 'BusKVVolt'])
    Bus_data = Bus_data.drop_duplicates(subset=["SubNum"])
    busdata = IDs.merge(Bus_data, how="inner", on="SubNum")
    buskv = busdata["BusKVVolt"].tolist()
    # Voltages = Bus_data['BusKVVolt']
    '''
    BuskV = []
    for busnum, volt in zip(Bus_data["SubNum"], Bus_data["BusKVVolt"]):
        for sub in subID:
            if busnum==sub:
                BuskV.append(volt)
    '''
    BuskV = np.asarray(buskv)
    BuskV = np.asfarray(BuskV, float)
    return BuskV


def setup_voltage_data_piecewise(pw, subID, Bus_data):
    # pw.SolvePowerFlow()
    # IDs=pd.DataFrame()
    # IDs["SubNum"]=subID
    # Bus_data = pw.GetParametersMultipleElement('load', ['SubNum', 'BusNum', 'BusKVVolt'])
    # Bus_data=Bus_data.drop_duplicates(subset=["SubNum"])
    BuskV = float(Bus_data.loc[Bus_data['SubNum'] == subID, 'BusKVVolt'])

    return BuskV


def compile_power(pw, Power):
    # get data into correct format
    # print("Power recieved is type: ", type(Power))
    # print("Power recieved is: ", Power)

    # print(Power)
    DSS = Power
    Data1 = DSS[DSS.find('['):]
    Data1 = Data1[1:-1]
    power = Data1.split(",")
    Power_data = []
    for item in power:
        if item != '':
            Power_data.append(float(item))

    # Power_data=ast.literal_eval(Power)
    # print("Power recieved is type: ", type(Power_data))
    P = 0
    Q = 0
    if len(Power_data) > 1:
        P = abs(Power_data[0]) / 1000
        Q = Power_data[1] / 1000
        check = True
    else:
        check = False
        # print("Unused Data", Power_data)
        P = 0
        Q = 0
    return P, Q, check


def add_transmission_EV(mw, ev_mw, ev_mvar):
    mw["LoadID"] = mw['Number of Bus'].astype(str) + " " + mw["Load ID"].astype(str)
    mw.set_index("LoadID", inplace=True, append=False, drop=True)
    mw = mw.drop(['Number of Bus', 'Load ID'], axis=1)
    # mvar["LoadID"] = mvar['Number of Bus'].astype(str) + " " + mvar["Load ID"].astype(str)
    # mvar.set_index("LoadID", inplace=True, append=False, drop=True)
    # mvar=mvar.drop(['Number of Bus', 'Load ID'], axis=1)

    ev_mw["LoadID"] = ev_mw['Number of Bus'].astype(str) + " " + ev_mw["Load ID"].astype(str)
    ev_mw.set_index("LoadID", inplace=True, append=False, drop=True)
    ev_mw = ev_mw.drop(['Number of Bus', 'Load ID'], axis=1)
    ev_mvar[['BusNum', 'Extra']] = ev_mvar['Number of Bus'].str.split(" ", 1, expand=True)
    ev_mvar["LoadID"] = ev_mvar['BusNum'].astype(str) + " " + ev_mvar["Load ID"].astype(str)
    ev_mvar.set_index("LoadID", inplace=True, append=False, drop=True)
    ev_mvar = ev_mvar.drop(['Load ID', 'BusNum', 'Extra', 'Number of Bus'], axis=1)
    '''
    mw.set_index(['Number of Bus', 'Load ID'], inplace=True, append=False, drop=True)
    mvar.set_index(['Number of Bus', 'Load ID'], inplace=True, append=False, drop=True)

    ev_mw.set_index(['Number of Bus', 'Load ID'], inplace=True, append=False, drop=True)
    ev_mvar.set_index(['Number of Bus', 'Load ID'], inplace=True, append=False, drop=True)
    '''
    # print("MW time Series")
    # print(mw)
    mw = mw.add(ev_mw, fill_value=0)
    # print(mw)
    # mvar=mvar.add(ev_mvar, fill_value=0)
    return mw


def add_transmission_EV_with_hold(mw, ev_mw_all, ev_mvar, hour):
    mw = mw[["Number of Bus", "Load ID", f"X{hour}"]]
    mw["LoadID"] = mw['Number of Bus'].astype(str) + " " + mw["Load ID"].astype(str)
    mw.set_index("LoadID", inplace=True, append=False, drop=True)
    mw = mw.drop(['Number of Bus', 'Load ID'], axis=1)
    # mvar["LoadID"] = mvar['Number of Bus'].astype(str) + " " + mvar["Load ID"].astype(str)
    # mvar.set_index("LoadID", inplace=True, append=False, drop=True)
    # mvar=mvar.drop(['Number of Bus', 'Load ID'], axis=1)
    #print("ev_mw_all Multipliers")
    ev_mw_all.to_csv(PARENT_DIRECTORY +"\\check_multiplies.csv")
    #ev_mw_all['Multipliers'] = ev_mw_all['Multipliers'].fillna(1)
    multipliers_trans = ev_mw_all["Multipliers"]
    # timeseriesMW_EV = timeseriesMW_EV.drop(['Multipliers', 'Hold_over'], axis=1)
    ev_mw = ev_mw_all[["Number of Bus", "Load ID", f"X{hour}"]]
    # ev_mw_all.to_csv(PARENT_DIRECTORY+f"\\EV_before{hour}.csv")
    ev_mw[f"X{hour}"] = (ev_mw[f"X{hour}"]) * multipliers_trans
    ev_mw_all[f"X{hour}"] = ev_mw[f"X{hour}"]
    # print("hold mult", 1-multipliers_trans)
    #if hour==24:
    #    multipliers_trans = ev_mw_all["Multipliers"].replace(0, 1)
    if hour < 24:
        ev_mw_all[f"X{hour + 1}"] = ev_mw_all[f"X{hour + 1}"] + ev_mw[f"X{hour}"] * (1 - multipliers_trans)
    # ev_mw_all.to_csv(PARENT_DIRECTORY+f"\\EV_after{hour}.csv")
    # print(f"EV {hour} after:", ev_mw[f"X{hour}"].sum(), f"EV {hour+1} after:", ev_mw_all[f"X{hour+1}"].sum())
    # print(f"EV {hour}:", ev_mw[f"X{hour}"].sum(), f"EV {hour+1}:", ev_mw_all[f"X{hour+1}"].sum())
    ev_mw["LoadID"] = ev_mw['Number of Bus'].astype(str) + " " + ev_mw["Load ID"].astype(str)
    ev_mw.set_index("LoadID", inplace=True, append=False, drop=True)
    ev_mw = ev_mw.drop(['Number of Bus', 'Load ID'], axis=1)
    ev_mvar[['BusNum', 'Extra']] = ev_mvar['Number of Bus'].str.split(" ", 1, expand=True)
    ev_mvar["LoadID"] = ev_mvar['BusNum'].astype(str) + " " + ev_mvar["Load ID"].astype(str)
    ev_mvar.set_index("LoadID", inplace=True, append=False, drop=True)
    ev_mvar = ev_mvar.drop(['Load ID', 'BusNum', 'Extra', 'Number of Bus'], axis=1)

    print("MW time Series")
    print(mw)
    mw = mw.add(ev_mw, fill_value=0)
    print("Trans Load:", mw)
    # mvar=mvar.add(ev_mvar, fill_value=0)
    return mw, ev_mw_all


def update_power(pw, P, Q, subID, opf_file, EV_loads, hour, T_EV, multipliers_t, hold):
    # pw.SolvePowerFlow()
    print("EV from Dist Length")
    print(len(P), len(subID))
    # pw.RunScriptCommand(f'SolvePrimalLP()')
    # pw.RunScriptCommand(f'SolvePrimalLP("", "D:\\Full-Co-Simulation\\transmission\\savelog.aux")')
    print("EV from Dist")
    print(P)
    print("EV sum from Dist")
    print(sum(P))
    # pw.RunScriptCommand(f'SolvePrimalLP("{opf_file}")')
    load_data = pw.GetParametersMultipleElement('load', ['SubNum', 'BusNum', 'LoadID', 'LoadMW', 'LoadMVR', 'BusPUVolt',
                                                         'Latitude:1', 'Longitude:1'])
    # print("Load data original")
    # print(load_data["LoadMW"])
    # load_data.to_csv(opf_file)
    # TkV69subs=np.zeros(len(load_data))
    # DkV69subs=np.zeros(len(load_data))
    # load_data.to_csv(PARENT_DIRECTORY + "\\Load_data_pre_change.csv")
    TkV69subs = []
    DkV69subs = []
    # print("size of kv69", len(kV69subs))
    # print("subID length is", len(subID))
    # print("P length is", len(P))
    ld = load_data.copy()

    '''
    for i in range(len(subID)):

        #print("PW Loads")
        #print(load_data.loc[load_data['SubNum'] == subID[i], 'LoadMW'])
        #TkV69subs[load_data['SubNum'] == subID[i]]=load_data.loc[load_data['SubNum'] == subID[i], 'LoadMW']
        TkV69subs.append(load_data.loc[load_data['SubNum'] == subID[i], 'LoadMW'])
        idx=load_data.index[load_data["SubNum"]==subID[i]].tolist()
        #print("count", i)
        #print("power", P[i])
        #print(type(idx))

        if len(idx)>1:
            for j in idx:
                #ld.loc[j, 'LoadMW'] = P[i]/len(idx) + load_data.loc[j, 'LoadMW']
                #print("load loc")
                #print(load_data.loc[j]["LoadMW"])
                ld.loc[j, 'LoadMVR'] = Q[i]#/len(idx) #+ load_data.loc[j, 'LoadMVR']
        elif idx:
            print("Original", ld.loc[idx[0], "LoadMW"])
            #print("idx", idx[0])
            #print("load loc2")
            #print(load_data.loc[idx[0]]["LoadMW"])
            #ld.loc[idx[0], 'LoadMW']= P[i]  + load_data.loc[idx[0], 'LoadMW']
            ld.loc[idx[0], 'LoadMVR'] = Q[i]  #+ load_data.loc[idx[0], 'LoadMW']
            print("After", ld.loc[idx[0], "LoadMW"])


        #load_data.loc[load_data['SubNum'] == subID[i], 'LoadMVR'] = Q[i]
        DkV69subs.append(load_data.loc[load_data['SubNum'] == subID[i], 'LoadMW'])
        #print("values",P[i], Q[i])
        #DkV69subs[load_data['SubNum'] == subID[i]]=load_data.loc[load_data['SubNum'] == subID[i], 'LoadMW']
    print("New Load")
    print(ld["LoadMW"])
    #load_data=load_data.fillna(0)
    ld2=ev_loads_d(EV_loads, hour, ld, opf_file, subID)
    ld2.to_csv(opf_file)
    #print("IS NULL",load_data.isnull().values.any())
    #load_data.to_csv(PARENT_DIRECTORY + "\\Load_data.csv")
    #ld.to_csv(opf_file)
    pw.change_and_confirm_params_multiple_element(ObjectType='load', command_df=ld2)
    pw.SolvePowerFlow()
    DkV69subs=pd.Series(DkV69subs)
    TkV69subs=pd.Series(TkV69subs)
    '''

    for k, p in zip(subID, P):
        # print("Iterator:", k)
        # print(len(subID))
        idx = load_data.index[load_data["SubNum"] == k].tolist()
        # print("IDX")
        # print(idx)
        if len(idx) > 1:

            # check_loads=load_data[load_data["SubNum"] == k]
            # check_loads=check_loads["LoadMW"].tolist()
            # id_p=check_loads.index(max(check_loads))
            # print(check_loads)
            # print("id_p:", id_p)
            # id=idx[id_p]
            # ld.loc[id, 'LoadMW'] = p + load_data.loc[idx[0], 'LoadMW']

            for j in idx:
                ld.loc[j, 'LoadMW'] = p / len(idx) + ld.loc[j, 'LoadMW']
                # print(ld.loc[j]['LoadMW'] )

        elif idx:
            ld.loc[idx[0], 'LoadMW'] = p + ld.loc[idx[0], 'LoadMW']
            # print(ld.loc[idx[0]]['LoadMW'])
        else:
            print("NO MATCH FOUND")
            print("SubID:", k)

    '''
    ev_total=0
    for k in T_EV:
        #print("Iterator:", k)
        #print(subID)
        idx = ld.index[load_data["SubNum"] == k].tolist()
        #print("IDX")
        #print(idx)
        EV_busloads=EV_loads[EV_loads["Substation Number"]==k]
        EV = EV_busloads["X"+str(hour)].sum()
        EV=round(EV, 1)
        #print("EV is:", EV, "at Substation:", k)
        ev_total=EV + ev_total
        #print("EV total is:", ev_total)

        if len(idx) > 1:

            for j in idx:
                ld.loc[j, 'LoadMW'] = EV/len(idx) + ld.loc[j, 'LoadMW']
                #print("ADDED LOAD:", ld.loc[j]['LoadMW'] -load_data.loc[j, 'LoadMW'])

        elif idx:
            ld.loc[idx[0], 'LoadMW'] = EV + ld.loc[idx[0], 'LoadMW']
            #print("ADDED LOAD:", ld.loc[idx[0]]['LoadMW'] - load_data.loc[idx[0], 'LoadMW'])
        else:
            print("NO MATCH FOUND")
            print("SubID:", k)
        '''
    # print("EV Total:", ev_total)
    ld2, new_hold = ev_loads_d(EV_loads, hour, ld, opf_file, T_EV, multipliers_t, hold)
    # ld2.to_csv(opf_file)
    # print("IS NULL",load_data.isnull().values.any())
    # load_data.to_csv(PARENT_DIRECTORY + "\\Load_data.csv")
    ld2.to_csv(opf_file)
    pw.change_and_confirm_params_multiple_element(ObjectType='load', command_df=ld2)
    pw.SolvePowerFlow()
    # load_data = pw.GetParametersMultipleElement('load', ['SubNum', 'BusNum', 'LoadID', 'LoadMW', 'LoadMVR', 'BusPUVolt', 'Latitude:1', 'Longitude:1'])
    # load_data.to_csv(opf_file)
    return new_hold


def csv_reader(master_csv):
    substations = pd.read_csv(master_csv)
    dsub = substations["D Sub"].values
    dcon = []
    for d in dsub:
        d = d.split('_')
        d = d[0] + "_69"
        dcon.append(d)

    stations = dsub
    Bus = dcon
    return dcon, dsub


def check_convergence(pw, Tkv69, Dkv69):
    # pw.SolvePowerFlow()
    pw.RunScriptCommand("SolvePrimalLP()")
    '''
    load_data = pw.GetParametersMultipleElement('load', ['BusNum', 'LoadID', 'LoadMW', 'LoadMVR'])
    PWMW = load_data['LoadMW']
    TOPF=PWMW
    DOPF=None
    '''
    load_data = pw.GetParametersMultipleElement('load', ['BusNum', 'LoadID', 'BusKVVolt'])
    PWKV = load_data['BusKVVolt']
    # convergence= max((TOPF - DOPF) + abs(Tkv69 - Dkv69))
    # while convergence>0.1:
    convergence = abs(Tkv69.subtract(Dkv69, fill_value=0))
    # pw.SolvePowerFlow()
    return convergence


def weather_gen(pw, GenP, weatherName):
    # kf=pw.get_key_fields_for_object_type('gen')
    # print("key fields", kf)
    # pw.SolvePowerFlow()
    gen_data = pw.GetParametersMultipleElement('Gen',
                                               ['BusNum', 'GenID', 'BusName', 'GenMWMax', 'GenMVRMax', 'GenICost'])
    genMax = gen_data.GenMWMax
    genName = gen_data.BusName
    '''
    for wname, GP in zip(weatherName, GenP):
        for i in range(len(genName)):
            if wname== genName.iloc(i):
                genMax.iloc(i)==GP

    gen_data['GenMWMax']=genMax
    '''
    for name, GP in zip(weatherName, GenP):
        gen_data.loc[gen_data['BusName'] == name, 'GenMWMax'] = GP
    # print(gen_data.loc[gen_data['BusName'] == name, 'BusName'] )
    pw.change_and_confirm_params_multiple_element(ObjectType='gen', command_df=gen_data)
    return


def ev_loads_d(EV_loads, hour, load_data, opf_file, subID, multipliers_t, hold_over):
    print(len(EV_loads))
    # EVT_loads = EV_loads["Substation Number", f"X{hour}"]
    print(EV_loads)
    total_EV = EV_loads["X" + str(hour)].sum()
    print(f"Total EV for {str(hour)}", total_EV)
    '''
    for subID, load in zip(EV_loads["Substation Number"], EV_loads["X"+str(hour)]):
        #print("i count is", i)
        print(f"SubID {subID}; EV: {load}")
        #TkV69subs[load_data['SubNum'] == subID[i]]=load_data.loc[load_data['SubNum'] == subID[i], 'LoadMW']
        load_data.loc[load_data['SubNum'] == subID, 'LoadMW'] = load_data.loc[load_data['SubNum'] == subID, 'LoadMW'] +load
    '''
    ld2 = load_data.copy()
    # subID=subID["Substation Number"]
    # subID=[*set(subIDs)]
    # subID=subIDs.drop_duplicates().values
    multiplier = multipliers_t["Multiplier"].values
    ev_total = 0
    new_hold = []
    count = 0
    print("Lengths", len(subID), len(multiplier), len(hold_over))
    for k, m, h in zip(subID, multiplier, hold_over):
        # print("Iterator:", k, "Multiplier", m)
        # print(subID)
        # print("Multiplier",m, "holdover", h)
        idx = load_data.index[load_data["SubNum"] == k].tolist()
        # print("IDX")
        # print(idx)
        EV_busloads = EV_loads[EV_loads["Substation Number"] == k]
        EV = (EV_busloads["X" + str(hour)].sum() + h) * m
        if m != 1:
            new_h = (EV_busloads["X" + str(hour)].sum() + h) * (1 - m)
            new_hold.append(new_h)
        #elif hour==24 and m==0:
        #    new_h = (EV_busloads["X" + str(hour)].sum() + h) * (1 - m)
        #    new_hold.append(new_h)
        else:
            new_h = h
            new_hold.append(new_h)
        if count == 0:
            print("EV", EV_busloads["X" + str(hour)].sum(), "EV w hold", EV, "Multiplier", m, "holdover", h, "New Hold",
                  new_h)
        count = count + 1
        # EV=round(EV, 2)
        # print("EV is:", EV, "at Substation:", k)
        ev_total = EV + ev_total
        # print("EV total is:", ev_total)

        if len(idx) > 1:
            '''
            check_loads=load_data[load_data["SubNum"] == k]
            check_loads=check_loads["LoadMW"].tolist()
            id_p=check_loads.index(max(check_loads))
            print(check_loads)
            id=idx[id_p]
            ld.loc[id, 'LoadMW'] = EV + load_data.loc[idx[0], 'LoadMW']
            '''
            for j in idx:
                ld2.loc[j, 'LoadMW'] = EV / len(idx) + load_data.loc[j, 'LoadMW']
                # print("ADDED LOAD:", ld.loc[j]['LoadMW'] -load_data.loc[j, 'LoadMW'])

        elif idx:
            ld2.loc[idx[0], 'LoadMW'] = EV + load_data.loc[idx[0], 'LoadMW']
            # print("ADDED LOAD:", ld.loc[idx[0]]['LoadMW'] - load_data.loc[idx[0], 'LoadMW'])
        else:
            print("NO MATCH FOUND")
            print("SubID:", k)

    # ld.to_csv(opf_file)
    print("Other total EV:", ev_total)
    print(f"EV Dist should be {str(hour)}", total_EV - ev_total)

    '''
    print(range(0,len(subID)))
    for m in range(len(subID)):
        print("Iterator:", m)
        idx = load_data.index[load_data["SubNum"] == subID[m]].tolist()
        print("sub ID")
        print(subID[m])
        EV_busloads=EV_loads[EV_loads["Substation Number"]==subID[m]]
        EV = EV_busloads["X"+str(hour)].sum()
        print("EV Load")
        print(EV)
        print("lengths:", len(load_data))
        if len(idx) > 1:
            print("idx")
            print(idx)

            for j in idx:
                print(ld.loc[j]['LoadMW'] )
                ld.loc[j, 'LoadMW'] = EV/len(idx) + load_data.loc[j, 'LoadMW']
                print(ld.loc[j]['LoadMW'] )
        elif idx:
            print("idx")
            print(idx[0])
            print("Load Before")
            print(load_data.loc[idx[0], 'LoadMW'] )
            ld.loc[idx[0], 'LoadMW'] = EV + load_data.loc[idx[0], 'LoadMW']
            print("Load after")
            print(ld.loc[idx[0]]['LoadMW'])
        '''

    return ld2, new_hold

