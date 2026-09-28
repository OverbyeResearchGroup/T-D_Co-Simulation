# helics_utils: HELICS federate wrapper

`__init__.py` wraps the HELICS Python API in a small `Federate` class. Both federates add the repository root to `sys.path` and import `setup_helics_federate` from this package (see the [root README](../README.md)). **Author (git history):** Diana Wallison, 2025.

## Files

| File | What it does |
|---|---|
| `__init__.py` | `Federate` creates a value federate on a ZMQ core named after the federate (core init string `--federates=1`, log level 7, time delta 1). It registers subscriptions and global publications (the data type is given by name, for example `"vector"`). `start()` enters executing mode, `advance(t)` requests time until the granted time passes `t`, `send()` publishes a vector or a double, and `recv()` reads an input as a string. The destructor disconnects and frees the federate and closes the HELICS library. `setup_helics_federate(federate_name, subscriptions, publications)` builds a `Federate`, registers the topics and starts it. |
| `__pycache__/` | Compiled files for Python 3.7, 3.10 and 3.12, committed to git. |

## Setup

Needs the `helics` Python package, which the root [`environment.yml`](../environment.yml) installs through pip (`helics==3.6.1`).

## Running

Not run directly. `distribution/main.py` and `transmission/transmission_cost.py` import it; start them through `run_cosim.bat` in the repository root.

## Inputs and outputs

No files. Values pass between federates through the HELICS broker.
