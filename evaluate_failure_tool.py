import os
import subprocess
import sys
import select
import git
from dateutil.parser import parse
import datetime
from envbash import load_envbash

class EvaluateFailure():
    def __init__(self):
        ''' 
        Class constructor
        '''

        # Directories and Paths
        # Please use absolute paths
        self.repos_file_path = ""
        self.autoware_path = ""
        self.scenario_file_path = ""
        self.osm_file_path = ""
        self.pcd_file_path = ""
        os.chdir(self.autoware_path)
        print("The Current working directory now is: {0}".format(os.getcwd()))

        # Time period for searching
        self.date_to_stop_searching = "" #Please write it in format of "year-month-day" like that "2023-09-31"
        
        
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
        

    def get_repos_paths(self):
        ''' 
        TBD
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
                if ' ' in res or "simulator" in res:
                    continue
                self.repos_path.append(self.autoware_path+"/src/"+res)
        #print(res)
            return self.repos_path
        
    def split_log_info(self, repo_log):
        ''' 
        TBD
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
        TBD
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
        TBD
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
        TBD
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
        TBD
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
        TBD
        '''
        cmd = ["rm","-r","build/","install/", "log/"]
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd)
        return stdout, stderr
    
    def compile_autoware(self):
        ''' 
        TBD
        '''
        cmd = ["colcon","build","--symlink-install","--cmake-args", "-DCMAKE_BUILD_TYPE=Debug", "-DCMAKE_EXPORT_COMPILE_COMMANDS=1"]
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd)
        print('Compilate Ended')
        return stdout, stderr

    def check_autoware_compile_output(self, compile_stdout):
        ''' 
        TBD
        '''
        for msg in compile_stdout:
            if "Aborted" in msg or "Failed" in msg:
                return False
        return True

    def source_autoware(self):
        ''' 
        TBD
        '''
        setup_script = self.autoware_path+"/install/setup.bash"
        load_envbash(setup_script, override=True)

    
    def import_repos(self):
        ''' 
        TBD
        '''
        cmd = "vcs import "+ self.autoware_path+"/src < "+ self.repos_file_path+ " && vcs pull "+ self.autoware_path+"/src"
        print(cmd)
        stdout, stderr = self.run_subprocess_with_capture_and_print(cmd, use_shell=True)
        print('Importing Ended')
        return stdout, stderr

    def run_scenario_simulator(self):
        ''' 
        TBD
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
        TBD
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
        TBD
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
    
    def create_last_changed_file(self, last_changed_repo, last_changed_commit):
        with open('last_changed_repo.txt','w') as last_changed_repo_file:
            last_changed_repo_file.write("Last changed repo was : " + last_changed_repo + "\nLast commit that was passing : "+ last_changed_commit)


    def create_mermaid_visualization(self):
        with open('README.md','w') as mermaid_vis_file:
            mermaid_vis_file.write("```mermaid\n")
            mermaid_vis_file.write("---\n")
            mermaid_vis_file.write("displayMode: compact\n")
            mermaid_vis_file.write("---\n")
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
                    if iterator == self.repos_currently_checkedout_index_dict[repo]:
                        mermaid_vis_file.write("    "+commit[:6]+" : crit, milestone, "+ str(dates[iterator])+ ", 4h\n")
                    else:
                        mermaid_vis_file.write("    "+commit[:6]+" : milestone, "+ str(dates[iterator])+ ", 4h\n")

                    iterator = iterator+1



    def run(self):
        ''' 
        TBD
        '''
        scenario_pass = False
        last_changed_repo = "empty"
        last_changed_commit = "empty"
        index = -1
        self.import_repos()
        self.get_repos_paths()
        self.get_repos_commits_dict()
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
                    last_changed_repo = repo
                    last_changed_commit = self.repos_commits_dict[repo][i]
                    index = i - 1
                    break
                    #create repos file
            if scenario_pass:
                break
        
        if scenario_pass == False :
            print("The script is not able to find the success/fail border")
        else:
            print("Last changed repo was : ", last_changed_repo)
            print("Last commit that was passing : ", last_changed_commit)
            self.create_mermaid_visualization()
            self.get_and_print_repos_before_first_success(index)
            self.create_failed_repo_file()
            self.create_last_changed_file(last_changed_repo, last_changed_commit)


if __name__ == "__main__":
    eval_fail = EvaluateFailure()
    eval_fail.run()
