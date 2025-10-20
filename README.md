# T-D_Co-Simulation
# Set-up Enviroment
The provided environment.yml file can be used to create a new “environment” that includes all the required dependencies for running the custom scripts. Two examples for creating this new environment—named “cympyEnv” here—are provided below:
Example directly in Python: python -m venv c:\path\to\environment.yml
Example with Anaconda Python: conda env create --name cympyEnv --file=c:\path\to\environment.yml
Once the cympyEnv has been created, it must be activated before running any of the custom scripts.
# Importing the CymPy Package
After creating and activating the cympyEnv, the steps below can be used to import the CymPy package:
1. Create a text file called “cympy.pth” that contains the path to the parent folder where the CymPy library is located (e.g., “C:\Program Files\CYME\CYME_9_4_rev01”). An example is provided.
2. Place “cympy.pth” in the “site-packages” folder of the cympyEnv environment (e.g., “C:\Users\...\Anaconda3\envs\cympyEnv\Lib\site-packages”)
3. Include “import cympy” at the top of any Python script for which the package will be used.

# Running the  Co-Simulation

- **Change any file reference to reflect their locations on your system (all folders not provided here should be placed in the main Co-Simulation Folder**
- **Change the directory in the Anaconda Prompt to the project location**
- **Run the simulation using the batch file (The file locations inside the batch files must be changed to match your system path)(Batch files can be edited with any text editor)**
```
cd CoSim Directory 
run_cosim.bat 
```
