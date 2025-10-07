
@echo on

call set EVfilepath=D:\CEII-Data\Texas_Co-Ops\Cyme Practice (Diana)\Co-Sim (Cyme)\10_simulation_output_combined_remap_D_Loads.csv
call echo EVfilepath
call helics run --path run.json 
call helics kill-all-brokers

	
