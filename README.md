# scenario-simulator-failure-evaluation-tool
This is the repository for scenario simulator failure evaluation tool. The tool aims to help autoware developers find the commit(s) that made a specific scenario fail.


~~~
This tool is still WIP.
It is expected to have improvements and fixes while testing it in different use cases.
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
- The tool supports both calling the script with passing needed arguments from the command line or setting these arguments in the class constructor.
- If the tool user would like to set the needed arguments in the class constructor, then s/he needs to open the python script, go to the class constructor which is `def __init__(self):` and assign values for paths and search date under the if statement `if number_of_arguments == 1:`
	-  `repos_file_path`
    
    	This is the path of the .repos file that includes the commits of the repos that you would like to start the evaluation process from.
	- `autoware_path`

    	This is the path of autoware in your local machine
	- `scenario_file_path`

    	This is the path of the failing scenario that would like to check which commits are causing this failure
	- `osm_file_path`

    	This is the osm map file used by this scenario
	- `pcd_file_path`

    	This is the pcd file associated with the used map file
	> All previous paths have to be in absolute paths
	- `date_to_start_searching`

    	This is the date you would like the tool to start searching for commits.


	- `date_to_stop_searching`

    	This is the date you would like the tool to stop searching for commits.

	> Dates should be in "year-month-day" like that "2023-09-31"

~~~
When using date_to_start_searching, all repos have to be in the correct branch before using them.
~~~

### Usage
- After cloning this repository, in a command line terminal go to the directory of the `scenario-simulator-failure-evaluation-tool`
- Make sure that the `evaluate_failure_tool.py` has the permission to be executed as a program.
- If you have set the arguments using code change in class constructor : 

  `python3 evaluate_failure_tool.py`
- If you would like to pass the arguments from command line (**order matters)**:
  
  `python3 evaluate_failure_tool.py repos_file_path autoware_path scenario_file_path osm_file_path pcd_file_path date_to_start_searching date_to_stop_searching`

> Please note the format of the arguments as mentioned in [initialization section](#initialization).


~~~
The tool does not perform any plausibility checks to the arguments passed from command line, except the number of arguments.
Till this moment, it is the responsibility of the tool user to make sure that arguments are in correct order, correct format, and making sense, otherwise the tool will either crash or provide wrong output.
~~~

### What is the expected output when a failing scenario becomes passing in one iteration ?
- The tool provides some output printed in command line that you can see directly after the tool finished execution. But more imprtantly, the tool organizes the output for the user in the following files
  - `$scenario_name$_failed_commits.repos`
 
	This is the .repos file that includes the commit ids that you use to start debugging autoware for that failing scenario. That means it includes the commit just before the successful trial.

  - `last_changed_repo.txt`

	This file includes the repo and commit id that are lately changed for the successful trial. That means, this is the commit that the tool just checked out, then the scenario passed.

  - `README.md`
    
	This is the mermaid visualization file that you can use to visualize the output of the evaluation process.


These files are located in `autoware_path` after execution is done.

### How to make a quick test ?
- Add a buggy commit to the autoware.universe that is making autoware keep the vehicle standstill in the start location.
- Stage and commit it to have the commit id.
- Go to the .repos file and replace the version of autoware.universe with your buggy commit id.
- You can use the files under `testing_files` folder and follow [Initialization](#initialization) then [Usage](#usage) sections.
- The output should be as described [here](#what-is-the-expected-output-when-a-failing-scenario-becomes-passing-in-one-iteration).

## What does the tool do for you ?
- The tool checks out the commits of all repositories specified in the .repos file, with nearest commit date to start date `date_to_start_searching`
- The tool adds the paths of osm and pcd files in the scenario yaml file so you do not need to do that manually.
- The tool cleans log, install, and build folders to start clean autoware compilation for your evaluation process
- If the .repos file is not making autoware compile successfully, the tool will terminate and print a message for you in the command line to check and try again.
- The tool sources the setup.bash file if autoware compilation is successful
- The tool runs scenario simulator with the provided scenario file and checks if the scenario with all its iterations is passing or not
- For the first time, if the scenario is passing with the repositories checked out at start date, the tool will let you know that it is already passing and no need to go over the repos.
- If the scenario is failing with the repositories checked out at start date (expected), the tool will start iterating over the repos going back one by one until it stops by the search date you provided `date_to_stop_searching`.
- Whenever the tool comes to a combination of commits that is making autoware not compiling, the tool does not invoke the scenario simulator.
- When the tool comes to a combination of commits that is compiling autoware successfully and passing in the scenario simulator, it stops the searching process and prints and creates the output for you.
- The tool provides a mermaid visualization for the Autoware user in order to easily check which commits were being used when the scenario passed

For more details about how the tool works, please check the [flowchart](#flowchart) section.

## Visualization
The visualization provided by scenario simulator failure evaluation tool is a simple representation of the different Autoware repositories and commits, indicating **_at the time of the scenario became successful_** which commit was checked out in different repositories, the commit that lastly checked-out that made the scenario successful, and the commit after it that is highly suspected to be the commit causing this failure.

The visualization depends on [mermaid gantt chart](https://mermaid.js.org/syntax/gantt.html) syntax.

> It is worth mentioning that visualization does not include any commits that are older than date to stop searching `date_to_stop_searching`. This trimming is necessary for having the visualization more making sense and comfortable for the user to understand, specially that we have noticed that there are some repositories that are not frequently changed, just had a single commit for very long time while we were doing some evaluation tests.

### How to visualize the provided output ?

- There are different methods (offline and online) to see the chart
  - You can drag and drop the visualization README.md file in vscode and open the preview of it. You will need to install an extension named `Mermaid Chart` to render it.
  - You can copy the content of the visualization README.md file and paste it to [mermaid live editor](https://mermaid.live/edit). You will need to remove only the first and last lines
	- First line : ` ```mermaid `
	- Last line : ` ``` `
  - You can push the visualization README.md file to github (your private repository for example) and github will render and show it for you.
### How to understand the provided visualization ?
- The visualization provides a chronological order of different commits in Autoware repos during the time period of our interest for our evaluation process.
- The horizontal rows are the repositories.
- The vertical lines are the dates
- Between every vertical line, there are rhombuses with 6 digits beside each rhombus.
  - These rhombuses are the commits for each repositories
  - The 6 digits are the commit IDs
  - They are organized from right to left in chronological order (newest to oldest)
  - The commits right to each vertical line are the commits pushed for this day.
- The following table explains the different colors you may see in the visualization chart

| Description      	| Shape   |
| ------------------   | ------ |
| A commit with blue rhombus is a commit in the history of this repository for this period of time 	| ![red_rhombus](./design/blue_rhombus.png) |
| A commit with red rhombus means this is the commit currently checked-out for this repo at the time that scenario became successful  	| ![red_rhombus](./design/red_rhombus.png) |
| A commit with white or gray rhombus and red border means this is the lastly checked-out commit that made this scenario successful  	| ![red_rhombus](./design/gray_rhombus.png) |
| A commit with bright blue rhombus is the commit after the one that made the scenario successful and it is the commit highly suspected to be the one causing this failure.  	| ![red_rhombus](./design/bright_blue_rhombus.png) |


## Flowchart
![flowchart](./design/flowchart.svg)

## Important Note about failures due to timeout:
- Autoware Evaluator assigns the value of `global_time_out` as 885 seconds (in lots of cases).
- This value will be different while testing in your local machine as it comes from main/master branch of scenario simulator launch file `scenario_test_runner.launch.py`
- If the failure is happening due to timeout, please make sure that this value in your local machine is the same as used in Autoware Evaluator test
- You can make sure of the value used for your scenario of interest by downloading the `SIMULATION LOG` file and check `global_time_out` value. This is an [example](https://evaluation.tier4.jp/evaluation/reports/235755a0-05bb-5a1e-bebc-d23f89c6ff5d/tests/40b8b073-8c7f-5c42-98e2-491ba4a82357/3bce2c77-443f-534f-b822-bbde1ac02adf/83ada411-24db-5032-9fbc-f90f60a7a268?project_id=awf) where you can download it.


## Open Topics / Suggestions to be discussed
- Make commit ids in visualization linked with the github link of this repository/commit with ability to double click and open it.
- Generate issues after the tool finishes execution
- CI/CD integration

