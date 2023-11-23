import os
import subprocess
import sys
import select
import git
from dateutil.parser import parse
import datetime
from envbash import load_envbash

class EvaluateFailure():
    def __init__(self, args):
        ''' 
        Class constructor

        Arguments
        ---------
        args : Arguments to be used based on its length in two cases, either setting arguments in the code or from command line

        Returns
        -------
        None
        '''
        number_of_arguments = len(args)
        if number_of_arguments == 1:
            # Please fill the following paths and dates if you are using the script
            # without passing these arguments from command line

            # # Please use absolute paths
            self.repos_file_path = ""
            self.autoware_path = ""
            self.scenario_file_path = ""
            self.osm_file_path = ""
            self.pcd_file_path = ""
            
            # Time period for searching
            self.date_to_start_searching = ""  #Please write it in format of "year-month-day" like that "2023-09-31"
            self.date_to_stop_searching  = ""  #Please write it in format of "year-month-day" like that "2023-09-31"
            
        elif number_of_arguments == 8:
            # These arguments are passed from command line
            self.repos_file_path = sys.argv[1]
            self.autoware_path = sys.argv[2]
            self.scenario_file_path = sys.argv[3]
            self.osm_file_path = sys.argv[4]
            self.pcd_file_path = sys.argv[5]
            self.date_to_start_searching = sys.argv[6]
            self.date_to_stop_searching = sys.argv[7]
            
        else:
            print("Number of arguments is not sufficient to run the evaluation systems")
            print("Please check the documentation and try again")
            sys.exit()

        self.init()

    def init(self):
        ''' 
        This is an initialization function that is used to initialzize common variables and data structures.
        This function is called by the class constructor before using any different functions of the class.

        Arguments
        ---------
        None

        Returns
        -------
        None
        '''
        os.chdir(self.autoware_path)
        print("The Current working directory now is: {0}".format(os.getcwd()))
        # Internal datastructures and variables
        self.repos_path = []
        self.repo_commits = []
        self.repo_dates = []
        self.max_repo_commits_length = 0
        self.repos_commits_dict={}
        self.repos_dates_dict={}
        self.repos_currently_checkedout_index_dict={}
        self.failed_repos_commits_dict={}
        self.clean_autoware_first_time = True
        self.last_changed_repo = "empty"
        self.last_changed_commit = "empty"


    def get_repos_paths(self):
        ''' 
        Format absolute repositories paths from .repos file

        Arguments
        ---------
        None

        Returns
        -------
        repos_path : array of strings
            array of absolute paths for different repositories found in .repos file
        '''
        with open(self.repos_file_path, "r") as file:
            repos_file_lines = file.readlines()
            sub1 = " "
            sub2 = ":"
            for s in repos_file_lines:
                res = ''
                try:
                    idx1 = s.index(sub1)
                    idx2 = s.index(sub2)
                except ValueError:
                    print("Oops!  That was no valid number.  Try again...")
                    continue
                for idx in range(idx1 + len(sub1) + 1, idx2):
                    res = res + s[idx]
                if ' ' in res:
                    continue
                self.repos_path.append(self.autoware_path+"/src/"+res)
        #print(res)
            return self.repos_path
        
    def split_log_info(self, repo_log):
        ''' 
        Helper function that is used to split any git repository log message based on commit
        Each commit log message is stored in any entery of log array

        Arguments
        ---------
        repo_log : string
            This is the text out of performing git log for a repository

        Returns
        -------
        splitted_log_info : array of strings
            array log info but splitted per commits, each commit log in one entry of the array
        '''
        delimiter = "\n\ncommit "
        counter = 0
        splitted_log_info = []
        for x in repo_log.split(delimiter):
            if counter == 0:
                splitted_log_info.append(x)
                counter = counter + 1
            else :
                splitted_log_info.append("commit "+x)
        
        return splitted_log_info
    
    def get_commits(self, splitted_log_info):
        ''' 
        Gets commit ids of a git repository based on its splitted log info

        Arguments
        ---------
        splitted_log_info : array of string
            Git repository log info but splitted per commit

        Returns
        -------
        commits : array of strings
            array contains the commit ids of this repository, each id in one entry of the array
        '''
        sub1 = "commit"
        sub2 = "\nAuthor"
        commits = []
        for s in splitted_log_info:
            res = ''
            try:
                idx1 = s.index(sub1)
                idx2 = s.index(sub2)
        
            except ValueError:
                print("Oops!  That was no valid number.  Try again...")
                continue
            for idx in range(idx1 + len(sub1) + 1, idx2):
                res = res + s[idx]
            # Sometimes there are a merge information between commit and auther.
            # It shows like that after the commit id "\nMerge: commit_id commit_id" 
            # So we need to check that and remove the merge info if exists
            if "Merge:" in res:
                res = res[:res.index("\n")]
            commits.append(res)
            #print(res)
        
        
        return commits
    
    def get_dates(self, splitted_log_info):
        ''' 
        Gets commits dates of a git repository based on its splitted log info

        Arguments
        ---------
        splitted_log_info : array of string
            Git repository log info but splitted per commit

        Returns
        -------
        dates : array of strings
            array contains the dates of commits of this repository, each date in one entry of the array
        '''
        sub1 = "Date:"
        sub2 = "\n\n"
        dates = []
        for s in splitted_log_info:
            res = ''
            try:
                idx1 = s.index(sub1)
                idx2 = s.index(sub2)
        
            except ValueError:
                print("Oops!  That was no valid number.  Try again...")
                continue
            for idx in range(idx1 + len(sub1) + 1, idx2):
                res = res + s[idx]
            dates.append(parse(res))
            #print(res)
        return dates
    
    def get_repos_commits_dates_dict(self):
        ''' 
        Formats dictonairy data strcutures needed for the evaluation process of the tool.
        Dictionary for repos and commit ids
        Dictionary for repos and commit dates
        Dictionary for repos and index of currently checked-out commit

        Arguments
        ---------
        splitted_log_info : array of string
            Git repository log info but splitted per commit

        Returns
        -------
        dates : array of strings
            array contains the dates of commits of this repository, each date in one entry of the array
        '''
        for repo_path in self.repos_path:
            #print(repo_path)
            repo_git = git.Git(repo_path)
            #print(repo_git.log(-1))
            repo_log_info = repo_git.log("--since="+self.date_to_stop_searching)
            if not repo_log_info:
                print(repo_path, "does not have any commits in the specified time period.\nTaking the current commit.")
                repo_log_info = repo_git.log(-1)
            #print(repo_log_info)
            splitted_log = self.split_log_info(repo_log_info)
            #print(splitted_log)
            #if  splitted_log:
            #print(len(splitted_log))
            repo_commits = self.get_commits(splitted_log)
            repo_dates = self.get_dates(splitted_log)
            if len(repo_commits) > self.max_repo_commits_length:
                self.max_repo_commits_length = len(repo_commits)
            print(repo_commits)
            #else:
            #   print(repo_path, " does not have any commits in this time period")
            print("------/////////////////**************\\\\\\\\\\\-----------")
            self.repos_commits_dict[repo_path] = repo_commits
            self.repos_dates_dict[repo_path] = repo_dates
            self.repos_currently_checkedout_index_dict[repo_path] = 0
        print("max_repo_commits_length = " , self.max_repo_commits_length)

    def run_subprocess_with_capture_and_print(self, cmd, use_shell=False):
        ''' 
        Runs a command line process and prints the output of this running process in terminal while running

        Arguments
        ---------
        cmd : array of string
            Command to be running

        use_shell : boolean
            A flag that helps the function handles some command line special characters (only if the command includes any)
        
        Returns
        -------
        stdout : array of strings
            array contains output of this process
        stderr : array of string
            array contains the errors of this process
        '''
        p = subprocess.Popen(cmd,shell=use_shell,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout = []
        stderr = []
        
        while True:
            reads = [p.stdout.fileno(), p.stderr.fileno()]
            ret = select.select(reads, [], [])
        
            for fd in ret[0]:
                if fd == p.stdout.fileno():
                    read = p.stdout.readline()
                    sys.stdout.write(read.decode())
                    stdout.append(read.decode())
                if fd == p.stderr.fileno():
                    read = p.stderr.readline()
                    sys.stderr.write(read.decode())
                    stderr.append(read.decode())
        
            if p.poll() != None:
                break
        
        return stdout, stderr
    
    def clean_autoware(self):
        ''' 
        Runs command for cleaning Autoware build, install, and log directories

        Arguments
        ---------
        None
        
        Returns
        -------
        stdout : array of strings
            array contains output of this process
        stderr : array of string
            array contains the errors of this process
        '''
        cmd = ["rm","-r","build/","install/", "log/"]
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd)
        return stdout, stderr
    
    def compile_autoware(self):
        ''' 
        Runs command for compiling Autoware

        Arguments
        ---------
        None
        
        Returns
        -------
        stdout : array of strings
            array of strings contains output of this process
        stderr : array of string
            array of strings contains the errors of this process
        '''
        cmd = ["colcon","build","--symlink-install","--cmake-args", "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_EXPORT_COMPILE_COMMANDS=1"]
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd)
        print('Compilate Ended')
        return stdout, stderr

    def check_autoware_compile_output(self, compile_stdout):
        ''' 
        Checks the output of Autoware compilation, if it is successful or not

        Arguments
        ---------
        compile_stdout : array of string
            array of strings contains output of Autoware compilation process
        
        Returns
        -------
        True/False
        '''
        for msg in compile_stdout:
            if "Aborted" in msg or "Failed" in msg:
                return False
        return True

    def source_autoware(self):
        ''' 
        Sources the needed enivronmental variables for Autoware

        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        setup_script = self.autoware_path+"/install/setup.bash"
        load_envbash(setup_script, override=True)

    
    def import_repos(self):
        ''' 
        Imports commit ids provided in the repo file

        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        cmd = "vcs import "+ self.autoware_path+"/src < "+ self.repos_file_path+ " && vcs pull "+ self.autoware_path+"/src"
        print(cmd)
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd, use_shell=True)
        print('Importing Ended')
        return stdout, stderr
    
    def checkout_at_start_date(self):
        ''' 
        Checks out repositories at a specific start date.

        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        for repo in self.repos_path:
            repo_git = git.Git(repo)
            branch_name = repo_git.branch()
            os.chdir(repo)
            cmd = "git checkout `git rev-list -n 1 --before="+ self.date_to_start_searching + " " + branch_name[2:]+"`"
            stdout, stderr = self.run_subprocess_with_capture_and_print(cmd, use_shell=True)
                   
        print('Checkout Ended')
        os.chdir(self.autoware_path)
        return stdout, stderr



    def run_scenario_simulator(self):
        ''' 
        Runs scenario simulator based on scenario, osm , and pcd provided.
        It edits the scenario file and write down the proper paths of osm and pcd.

        Arguments
        ---------
        None
        
        Returns
        -------
        stdout : array of strings
            array of strings contains output of this process
        stderr : array of string
            array of strings contains the errors of this process
        '''
        with open(self.scenario_file_path, "r") as file:
            data = file.readlines()
            count = 0
            for line in data:
                if "LogicFile:" in line:
                    print("found")
                    logic_file = True
                    data[count + 1] = "      filepath: "+self.osm_file_path+"\n"
                    logic_file_line_number = count + 1
                if "SceneGraphFile:" in line:
                    print("found")
                    scene_graphic = True
                    data[count + 1] = "      filepath: "+self.pcd_file_path+"\n"
                count = count + 1
            with open(self.scenario_file_path, "w") as output:
                output.writelines(data)
        
        cmd = ["ros2","launch","scenario_test_runner","scenario_test_runner.launch.py", "architecture_type:=awf/universe", 
        "record:=false", "scenario:="+self.scenario_file_path,
        "sensor_model:=sample_sensor_kit", "vehicle_model:=sample_vehicle"]
        
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd)
            
        print("Scenario Simulator Run Ended")
        return stdout, stderr
    
    def check_scenario_simulator_output(self, sim_stdout):
        ''' 
        Checks the output of scenario simulator run, if it is successful or not

        Arguments
        ---------
        sim_stdout : array of string
            array of strings contains output of scenario simulator run process
        
        Returns
        -------
        True/False
        '''
        number_of_scenarios = 0
        number_of_successful_scenarios = 0
        for msg in sim_stdout:
            if "Shutting down Autoware: (3/3) Waiting for Autoware to be exited" in msg :
                number_of_scenarios = number_of_scenarios + 1
            if "Passed" in msg :
                number_of_successful_scenarios = number_of_successful_scenarios + 1
        if number_of_scenarios > 0:
            if number_of_scenarios == number_of_successful_scenarios:
                return True
        return False
    
    def get_and_print_repos_before_first_success(self, index):
        ''' 
        This function finds and prints group of commits before scenario is firstly successful.
        These commits are highly suspected for root cause of failure.

        Arguments
        ---------
        index : int
            Number of iteration in which scenario turned into succesful
        
        Returns
        -------
        None
        '''
        for repo in self.repos_commits_dict.keys():
            commit = "empty"
            repo_base_name = os.path.basename(os.path.normpath(repo))
            if index > len(self.repos_commits_dict[repo]) - 1 :
                commit = self.repos_commits_dict[repo][len(self.repos_commits_dict[repo]) - 1]
                self.failed_repos_commits_dict[repo_base_name] = commit
            else :
                commit = self.repos_commits_dict[repo][index]
                self.failed_repos_commits_dict[repo_base_name] = commit
            print("Repo Name : ", repo_base_name, "\nCommit ID : ", commit)
            print("--------////-------")

    def create_failed_repo_file(self):
        ''' 
        Creates .repos file with commits that are highly suspected to be causing the scenario failure
        These commits are just before the scenario turned into successful.
        The .repos file is saved in the same autoware_path.

        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        failed_scenario_name = os.path.basename(os.path.normpath(self.scenario_file_path))
        failed_dotrepos_file_name = "scenario_"+failed_scenario_name+"_failed_commits.repos"
        version = "empty"
        # open both files 
        with open(self.repos_file_path,'r') as original_dotrepos_file, open(failed_dotrepos_file_name,'w') as failed_dotrepos_file: 
            # read content from original file 
            for line in original_dotrepos_file:
                if "version:" in line:
                    line = "    version: "+commit_id+"\n"
                    failed_dotrepos_file.write(line)
                    continue
                for repo in self.failed_repos_commits_dict.keys():
                    if repo in line:
                        commit_id = self.failed_repos_commits_dict[repo]
                        break

                # write content to new file  (failed repos)
                failed_dotrepos_file.write(line)
    
    def create_last_changed_file(self):
        ''' 
        Creates a txt file that indicates the repo name with its commit id that was recently changed nad turned
        the scenario into successful.
        
        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        with open('last_changed_repo.txt','w') as last_changed_repo_file:
            last_changed_repo_file.write("Last changed repo was : " + self.last_changed_repo + "\n")
            last_changed_repo_file.write("Last commit that was passing : "+ self.last_changed_commit + "\n")


    def create_mermaid_visualization(self):
        ''' 
        Creates a readme file that includes mermaid syntax for visualizing the different repos and commit ids within the specified period.
        The visualization highlights the commits that are recently checked-out. 
        As well, it highlights the lastly checked-out commit that turned the scenario into successful
        
        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        with open('README.md','w') as mermaid_vis_file:
            mermaid_vis_file.write("```mermaid\n")
            mermaid_vis_file.write("gantt\n")
            mermaid_vis_file.write("    title Scenario Simulator Failure Evaluation Tool Visualization Sample Output\n")
            mermaid_vis_file.write("    dateFormat YYYY-MM-DD HH:mm:ss\n")
            mermaid_vis_file.write("    axisFormat %Y-%m-%d %X\n")    
            mermaid_vis_file.write("    tickInterval 1day\n")
            for repo in self.repos_commits_dict.keys():
                dates = self.repos_dates_dict[repo]
                iterator = 0
                mermaid_vis_file.write("    section "+os.path.basename(os.path.normpath(repo))+"\n")
                for commit in self.repos_commits_dict[repo]:
                    if dates[iterator].date() <  datetime.datetime.strptime(self.date_to_stop_searching, '%Y-%m-%d').date():
                        continue
                    if repo == self.last_changed_repo:
                        if iterator == self.repos_currently_checkedout_index_dict[repo]:
                            mermaid_vis_file.write("    "+commit[:6]+" : done, crit, milestone, "+ str(dates[iterator])+ ", \n")
                        if iterator == self.repos_currently_checkedout_index_dict[repo] - 1:
                            mermaid_vis_file.write("    "+commit[:6]+" : active, milestone, "+ str(dates[iterator])+ ", \n")
                        else:
                            mermaid_vis_file.write("    "+commit[:6]+" : milestone, "+ str(dates[iterator])+ ", \n")
                    else:
                        if iterator == self.repos_currently_checkedout_index_dict[repo]:
                            mermaid_vis_file.write("    "+commit[:6]+" : crit, milestone, "+ str(dates[iterator])+ ", \n")
                        else:
                            mermaid_vis_file.write("    "+commit[:6]+" : milestone, "+ str(dates[iterator])+ ", \n")

                    iterator = iterator+1
            mermaid_vis_file.write("```\n")



    def run(self):
        ''' 
        This is the main run function of the tool that calls different other functions.
        It is used as well to handle the logic behind checking out process.
        
        Arguments
        ---------
        None
        
        Returns
        -------
        None
        '''
        scenario_pass = False
        index = -1
        #self.import_repos()
        self.get_repos_paths()
        self.checkout_at_start_date()
        self.get_repos_commits_dates_dict()
        if self.clean_autoware_first_time:
            self.clean_autoware()
        compile_stdout, compile_stderr = self.compile_autoware()
        compile_pass = self.check_autoware_compile_output(compile_stdout)
        if not compile_pass:
            print("Autoware is not compiling with your original repos file. Please check carefully then run the tool")
            sys.exit()
        self.source_autoware()
        sim_stdout, sim_stderr = self.run_scenario_simulator()
        sim_pass = self.check_scenario_simulator_output(sim_stdout)
        if sim_pass:
            print("Sceanrio is already passing with origina .repo file you are using. No need to go through repos throught specified time period")
            sys.exit()
        else :
            print("Scenario is really failing with your original .repo file. We will go through repos during the specificied time period")

        for i in range(1, self.max_repo_commits_length):
            for repo in self.repos_commits_dict.keys():
                if len(self.repos_commits_dict[repo]) == 1 or i > len(self.repos_commits_dict[repo])-1:
                    continue
                print("Checking out repo", repo, "of commit id ", self.repos_commits_dict[repo][i])
                repo_git = git.Git(repo)
                repo_git.checkout(self.repos_commits_dict[repo][i])
                current_repo_checkedout_index = self.repos_currently_checkedout_index_dict[repo] + 1
                self.repos_currently_checkedout_index_dict[repo] = current_repo_checkedout_index
                #compile
                print("Compiling Autoware")
                compile_stdout, compile_stderr = self.compile_autoware()
                compile_pass = self.check_autoware_compile_output(compile_stdout)
                #if compile fail .. continue
                if not compile_pass:
                    continue
                #self.source_autoware()
                # run sim
                print("Running Scenario Simulator")
                sim_stdout, sim_stderr = self.run_scenario_simulator()
                # check if all iterations pass
                sim_pass = self.check_scenario_simulator_output(sim_stdout)
                if sim_pass:
                    print("Found the repos that made the scenario pass with all iterations")
                    scenario_pass = True
                    self.last_changed_repo = repo
                    self.last_changed_commit = self.repos_commits_dict[repo][i]
                    index = i - 1
                    break
                    #create repos file
            if scenario_pass:
                break
        
        if scenario_pass == False :
            print("The script is not able to find the success/fail border")
        else:
            print("Last changed repo was : ", self.last_changed_repo)
            print("Last commit that was passing : ", self.last_changed_commit)
            self.create_mermaid_visualization()
            self.get_and_print_repos_before_first_success(index)
            self.create_failed_repo_file()
            self.create_last_changed_file()


if __name__ == "__main__": 
    eval_fail = EvaluateFailure(sys.argv)
    eval_fail.run()
