#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import os
from os import walk
from ConfigParser import ConfigParser
from datetime import datetime
import re
from time import sleep
import config_parser as CP
import start_fw
import ahtapot_utils
from dmrlogger import Syslogger
from dmrlogger import Filelogger
import sys


abs_path = os.path.abspath(__file__)
path_list = abs_path.split("/")
del path_list[-1]
path_name = "/".join(path_list)
full_path = path_name + "/"

if os.path.exists(full_path + "current_user.dmr"):
    with open(full_path + "current_user.dmr") as current_user:
        user = current_user.readline()
else:
    user = subprocess.check_output(["whoami"])

filelogger = Filelogger("FWBUILDER-AHTAPOT",'%(asctime)s %(name)s %(levelname)s %(message)s',"/var/log/ahtapot/gdys-gui.log","a",user)

def add_kerneltz(folder_path, file_name):

    try:
        cp_file = folder_path + file_name + ".tmp"
        org_file = folder_path + file_name
        p = subprocess.Popen(["grep","m time --kerneltz",org_file], stdout=subprocess.PIPE)
        out, err = p.communicate()
        if len(out) == 0:
            sed_cmd = "sed \"s/ -m time / -m time --kerneltz /g\" " + org_file + " > " + cp_file + " ; mv " + cp_file + \
                  " " + org_file
            subprocess.call([sed_cmd], shell=True)
    except Exception as e:
        filelogger.send_log("error"," while adding --kerneltz parameter : "+str(e))

def main():
    fw_path = CP.get_configs()['fw_path']
    git_master_branch = CP.get_configs()['git_master_branch']
    git_project_id = int(CP.get_configs()['git_project_id'])
	
	files = []
    for (dirpath, dirnames, file_names) in walk(fw_path):
        files.extend(file_names) #get filenames
        break
    for x in files:
        f_name, f_extension = os.path.splitext(x)
        if f_extension == ".fw":
            add_kerneltz(fw_path, x)
    #check if git runs correctly
    if ahtapot_utils.check_git_status(fw_path)==False:
        print "Git ile ilgili bir hata mevcut, 'git status' komutuyla kontrol ediniz."
        filelogger.send_log("error"," there is an error about git path please check with git status")
        sleep(5)
        exit()
        #start_fw.kill_fw()

    if ahtapot_utils.check_git_status(fw_path) != True:
        #create commits for every modified file and push
        date = datetime.strftime(datetime.now(),'%d/%m/%Y %H:%M:%S')
        ahtapot_utils.commit_files(fw_path,ahtapot_utils.get_changed_files(fw_path),date,git_master_branch)
        filelogger.send_log("info"," committed and pushed changes to repo")

        print u"Hatasiz Tamamlandi."
        print u"Firewall Builder 15 saniye sonra kapanacaktir..."
        sleep(15)
        filelogger.send_log("info"," killed Firewall Builder after install")
        start_fw.kill_fw()
    else:
        print u"Herhangi Bir Degisiklik Mevcut Degil."
        print u"Firewall Builder 15 saniye sonra kapanacaktir..."
        sleep(15)
        filelogger.send_log("warning"," No Change and killed Firewall Builder")
        start_fw.kill_fw()

if __name__=="__main__":
    main()
