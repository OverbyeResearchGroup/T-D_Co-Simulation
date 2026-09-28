# distribution: CYME distribution federate

`main.py` is the distribution side of the HELICS co-simulation described in the [root README](../README.md). It opens a CYME study through the `cympy` API, runs a load flow each hour, publishes the kW of every spot load to the transmission federate, and receives bus voltages back. After the 24-hour loop it writes CYME summary, overload, line-loading and voltage reports, if the last voltage string it received contains a comma. `cyme_functions.py` is a separate CYME test script and function library. **Author (git history):** Diana Wallison, 2025.

## Files

| File | What it does |
|---|---|
| `main.py` | HELICS federate `distribution_system`. Opens `testing_cyme_fullbonnet_file_10_net.xst` from this folder, subscribes to `distribution_system_voltage`, and publishes `transmission_system_load` (vector). Each hour: CYME load flow, a table of `TotalKW` and `TotalKVAR` for every spot load (also saved to `test.csv`), publish the kW list, wait for the voltages, call `update_load()`, run the load flow again. After the loop, if the last received voltage string contains a comma: `summary_for_network()` (called twice), `report_overloads_by_network_and_source()`, `report_all_overloads_and_line_loadings()` and `report_all_voltages()`. |
| `cyme_functions.py` | CYME helpers: build a study from a CYME database (`load_database_create_study`), open a study, list loads, add a spot load, query node information, and write summary, overload, line-loading and voltage CSV reports. Its `__main__` block opens the same study and writes `test_line_loading_all.csv` and `test_voltage_summary.csv` into this folder. `main.py` does not import it; `main.py` has its own copies of several of these functions. |
| `power_world_setup.py` | PowerWorld helpers written for the `esa` package (`setup_voltage_data`, `compile_power`, `update_power`, `csv_reader`). No script in this repository imports it. |
| `load_data_dummy_data.csv` | 16 node IDs (`Node ID`) with placeholder load values in columns `1` to `24`. Read by `main.py`. |

## Known issues

- `update_load()` does not apply the hourly loads. It returns after checking the first row of the load table, and when a node ID matches a spot load it reads `.Location` from the numeric load value, which raises `AttributeError`.
- The output folders are not created. Each `if not <folder>:` test checks a non-empty string, so `os.makedirs` never runs. Create `Summary`, `Overload Summary`, `Overloads` and `Voltages` under `Co-Simulation-Results\<date>\` in the repository root before a run.
- `system = "base"` does not run. `evfile` is set only when `system` is not `"base"`, but the main block always reads it, so Python raises `NameError`.
- `main.py` reads the `EVfilepath` environment variable at start-up and raises `KeyError` if it is not set. `run_cosim.bat` in the root sets it.
- `main.py` imports `dss` and `opendssdirect`, which `environment.yml` does not include. Install `dss-python` and `OpenDSSDirect.py`. The only OpenDSS call is `odd.Loads.AllNames()`, and its result is not used.

## Setup

Use the conda environment from the root [`environment.yml`](../environment.yml), plus `pip install networkx dss-python OpenDSSDirect.py`. `power_world_setup.py` imports `esa`, which `environment.yml` does not include; install it only if you use that file. The scripts also need CYME with its Python API: copy an edited `cympy.pth` into the environment's `site-packages` so `import cympy` works (steps in the [root README](../README.md)). Both scripts also run `import _db`; that module is not in this repository or in `environment.yml`, so it must be importable in the same environment. Windows only (paths use backslashes).

## Running

`main.py` runs as a HELICS federate. Start it through `run_cosim.bat` from the repository root, after fixing the `run.json` path (see the root Known issues). It needs the HELICS broker and the transmission federate.

Edit before a run:

- `studyFilename` in the `__main__` block (default `\testing_cyme_fullbonnet_file_10_net.xst`, read from this folder).
- `system`, `date` and `duration` at the top of the file. `date` only names the output folder; `duration = 25` gives hours 1 to 24.

To run the CYME test script on its own, from the repository root:

```
python distribution\cyme_functions.py
```

## Inputs and outputs

Inputs:

- CYME study `testing_cyme_fullbonnet_file_10_net.xst` in this folder (not in the repository).
- `load_data_dummy_data.csv` in this folder.
- The EV load CSV named by `EVfilepath` (columns `Node Name` and `X1` to `X24`). `main.py` prints its hourly total only.
- The voltage vector received on `distribution_system_voltage`. It is printed and parsed but not written into the CYME model.

Outputs of `main.py`:

- Once, after hour 24 and only if the last received voltage string contains a comma, in `Co-Simulation-Results\<date>\` under the repository root: `Summary\summary_X24.csv` (worst under and over voltage, counts, losses and fault currents per network), `Overload Summary\overload_summary_by_network_X24.csv` and `overload_summary_by_source_X24.csv`, `Overloads\all_overloads_X24.csv` (overhead by-phase lines with any positive `OverloadAmps` value), `Overloads\line_loading_X24.csv` (every overhead by-phase line, each `OverloadAmps` value plus 100), and `Voltages\all_voltages_X24.csv` (the CYME `VBase` value per device).
- `test.csv` in the working directory, overwritten each hour.

Outputs of `cyme_functions.py` (`__main__`): `test_line_loading_all.csv` and `test_voltage_summary.csv` in this folder.
