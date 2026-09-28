# transmission: PowerWorld transmission federate

`transmission_cost.py` is the transmission side of the HELICS co-simulation described in the [root README](../README.md). It opens a PowerWorld case through SimAuto. For each of 24 hours it sets load MW and MVAR from time-series files, sets the maximum MW of the generators listed in a weather file, publishes bus voltages for the mapped substations, and passes the load values it receives from the distribution federate to `update_power()`. As committed, that call fails in hour 1 (see Known issues). **Author (git history):** Diana Wallison, 2025.

## Files

| File | What it does |
|---|---|
| `transmission_cost.py` | Entry point and HELICS federate `transmission_system`. At import it opens `Texas7k_20221101_WithPFWModels_loadscaledmidnight.pwb` from this folder, reads `Substation Number` from `../dummy_list_mapped_system.csv`, and reads `MWtimeseries_<date>.csv` and `MVARtimeseries_<date>.csv` from this folder. It subscribes to `transmission_system_load` and publishes `distribution_system_voltage` (vector). Each hour: read bus voltages, set load MW and MVAR from column `X<hour>`, apply the weather file, publish the voltages, receive the load vector, call `update_power()`, save the PowerWorld log and a generator table. `get_weather_buses()` is defined but not called. |
| `power_world_setup.py` | Helper functions. Used by `transmission_cost.py`: `setup_voltage_data()` (`BusKVVolt` of the first load record at each listed substation number), `weather_gen()` (sets `GenMWMax` for generators matched by bus name), and `update_power()` (adds each received value to `LoadMW` of the load with the lowest nominal voltage at the substation in the same list position, writes the load table to CSV, changes the loads in PowerWorld, and runs `SolvePowerFlow`). Imported but not called: `compile_power()`, `csv_reader()`, `check_convergence()`. Not used: `setup_voltage_data_piecewise()`, `add_transmission_EV()`, `add_transmission_EV_with_hold()`, `ev_loads_d()`. |
| `saw_editing_file.py` | Local copy of the `SAW` (SimAuto wrapper) class from [ESA](https://github.com/mzy2240/ESA), with ESA's docstrings. It matches `esa/saw.py` in esa 1.3.5 except that the module docstring and the import of ESA's `initialize_bound` and `calculate_bound` helpers are removed. Connects to PowerWorld through COM (`pywin32`). Also imports `networkx`, `scipy`, `toolz` and `tqdm`, and uses `numba` if it is installed. |

## Known issues

- `transmission_cost.py` calls `update_power(pw, P, IDs, opf_file)` with four arguments, but `update_power()` takes nine (`pw, P, subID, opf_file, EV_loads, hour, T_EV, multipliers_t, hold`). The script stops with a `TypeError` in hour 1, after it receives the first load vector.
- The distribution federate sends CYME `TotalKW` values. `update_power()` adds them to PowerWorld `LoadMW` with no unit conversion.
- The weather lookup builds time strings such as `8/6/2021  13:00:00 PM` (two spaces, and hours above 12 marked PM). The `renewable_generation_Aug. 6.csv` in EV-Research-Simulations stores times as `8/6/2021 0:00`, so with that file no rows match and no generator limits change.
- `saw_editing_file.py` imports `networkx`, which the root `environment.yml` does not include. Install it with `pip install networkx`.

## Setup

Windows with PowerWorld Simulator and SimAuto. Use the conda environment from the root [`environment.yml`](../environment.yml), plus `pip install networkx`. `pywin32`, `numpy`, `pandas`, `scipy`, `toolz`, `tqdm` and `helics` come from `environment.yml`.

## Running

`transmission_cost.py` runs as a HELICS federate. Start it through `run_cosim.bat` from the repository root (see the root README). It imports `saw_editing_file` and `power_world_setup` by module name, which works because Python puts the script's own folder on `sys.path` when `run.json` launches `python transmission/transmission_cost.py`.

Edit before a run (top of `transmission_cost.py`):

- `pw_file`: the PowerWorld case in this folder.
- `date`: `'Aug. 6'` in the repository. It selects `MWtimeseries_<date>.csv`, `MVARtimeseries_<date>.csv`, `weather/renewable_generation_<date>.csv` and the output folder. `'Oct 16'` switches the weather date to 10/16/2021; any other value uses 8/6/2021.
- `weather`: `True` applies the weather file and writes the OPF and generator outputs under `Weather_data_added`. The weather file is read each hour and the log files go to `Weather_data_added` whatever the value.

## Inputs and outputs

Inputs (the files in the first three items are not in this repository; files with these names are in `Full-Co-Simulation/transmission/` of [EV-Research-Simulations](https://github.com/OverbyeResearchGroup/EV-Research-Simulations), where the case file has the extension `.PWB`):

- `Texas7k_20221101_WithPFWModels_loadscaledmidnight.pwb` (PowerWorld case).
- `MWtimeseries_<date>.csv` and `MVARtimeseries_<date>.csv` (columns `X1` to `X24`, matched to the case's loads by row position).
- `weather/renewable_generation_<date>.csv` (columns `DateTime`, `GenNamepw`, `MaxMW` are used).
- `../dummy_list_mapped_system.csv` (in the repository root; `Substation Number` column).
- The load vector received on `transmission_system_load`.

Outputs, each hour, in `Co-Simulation-Results\<date>\Weather_data_added\` under the repository root (the script creates the folders). As committed, the run stops at the `update_power()` call in hour 1 (see Known issues), so these files appear only after that call is fixed:

- `OPF\opf_load_data_X<hour>.csv`: the load table after the received values are added. The folder is named OPF, but the active code runs a power flow (`SolvePowerFlow`).
- `log<hour>.txt` and `log_after<hour>.txt`: the PowerWorld message log.
- `Generator_data\generator_data_hour_X<hour>.csv`: generator MW, MVR and limits.
