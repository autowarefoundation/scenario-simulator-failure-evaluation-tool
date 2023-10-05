# scenario-simulator-failure-evaluation-tool
This is the repository for scenario simulator failure evaluation tool. The tool aims to help autoware developers find the commit(s) that made a specific scenario fail.


~~~
This tool is still WIP and it is expected to have improvements and fixes while testing it in different use cases
~~~

## How to use 
### Prerequisites
- It is assumed that the tool user is using Ubuntu 22.04 with Python3 already installed
- It is assumed as well that the tool user has `pip3` installed. If not, you can install it using : 

    `sudo apt install python3-pip`
- It is required to install `GitPython` using :

    `pip3 install gitpython`
- It is required to install `envbash` using :

    `pip3 install envbash`

### Initialization
- The tool will support in very soon future getting arguments from command line.
- But, till that time, the tool user will need to open the python script, got to class constructor which is `def __init__(self):` and assign values for paths and search date.
    -  `repos_file_path`
    
        This is path of the .repos file that includes the commits of the repos that you would like to start the evaluation process from.
    - `autoware_path`

        This is the path of autoware in your local machine
    - `scenario_file_path` 

        This is the path of the failing scenario that would like to check which commits are causing this failure
    - `osm_file_path`

        This is the osm map file used by this scenario
    - `pcd_file_path`

        This is the pcd file associated with the used map file
    > All previous paths have to be in absolute paths
    - `date_to_stop_searching`

        This is the date you would like the tool to stop searching for commits. This is the date you believe autoware was passing for that specific scenario and tool will start to search when it starts to fail starting from the commits you provided in the .repos file back to this date.

### Usage
- From command line, go to the directory of the `scenario-simulator-failure-evaluation-tool`
- Make sure that the `evaluate_failure_tool.py` has the permission to be executed as program.
- Then type `python3 evaluate_failure_tool.py`

### What does the tool do for you ?
- The tool checks out the commits specified by the .repos file
- The tool cleans log, install, and build folder to start clean compilate for your evaluation process
- If the .repos file is not making autoware compile successfully, the tool will terminate and print a message for you in command line to check and try again.
- The tool sources the setup.bash file if autoware compilate is successful
- The tool run scenario simulator with the provided scenario file and checks if the scenario with all its iterations is passing or not
- If the scenario is passing with your .repos file, the tool will let you know that it is already passing and no need to go over the repos.
- If the scenario is already failing with your .repos file (expected), the tool will start iterating over the repo going back one by one until it stops by the search date you provided.
- Whenever the tool comes to a combination of commits that is making autoware not compiling, the tool does not invoke scenario simulator
- When the tool comes to a combination of commits that is compiling autoware successfully and passing in scenario simulator, it stops the searching process and prints and creates the output for you.

### What is the expected output when a failing scenario becomes passing in one iteration ?
- The tool provides the output printed in command line and same information in two separate files.
  - `last_changed_repo.txt`

    This file includes the repo and commit id that are lately changed for the successful trial. That means, this is the commit that the tool just checked out, then the scenario passed.
  - `$scenario_name$_failed_commits.repos`
  
    This is the .repos file that includes the commit ids that you use to start debuggin autoware for that failing scenario. That means it includes the commit just before the successful trial.

Both two files are located in `autoware_path` after execution is done.

    

TO-DO:
- Investigate global timeout
- Enable passing arguments to the python script instead of initializing variables in the class constructor
- Complete the functions description instead of TBD
- Draw a flowchart explaining how the tool works
- Visualization

