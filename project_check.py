#!/usr/bin/env python
#coding:utf8

import os
import sys
import yaml
import re
from optparse import OptionParser
from subprocess import call 

global return_code
global project_path
global script_path

script_path = (os.path.dirname(os.path.realpath(__file__)))

GREEN_COLOR='\x1b[6;30;42m'
RED_COLOR='\x1b[6;30;41m'
RESET_COLOR='\x1b[0m'

def check_args():
  global return_code
  global project_path

  parser = OptionParser()
  parser.add_option("-p", "--project_path", dest="project_path",
                  help="path to the project")
  (options, args) = parser.parse_args()

  if options.project_path is None:
    print "ERROR:property project_path is mandatory, exiting ..."
    sys.exit(2)

  if not os.path.exists(options.project_path):
    print "ERROR:path {} not valid".format(options.project_path)
    sys.exit(2)
  else:
    project_path=options.project_path

def yaml_load(filename):
  with open(filename, 'r') as stream:
      try:
          return (yaml.load(stream))
      except yaml.YAMLError as exc:
          print(exc)

def _check_file_exist_not_empty(current_file):
  global project_path
  global return_code
  try:
    assert(os.path.exists(current_file)), RED_COLOR + "file {} not found".format(current_file) + RESET_COLOR
    assert(os.path.getsize(current_file) > 0), RED_COLOR + "file {} is empty".format(current_file) + RESET_COLOR
  except (AssertionError, OSError) as e:
    return_code = 2
    print e

def check_default_files():
  global return_code
  global project_path

  _check_file_exist_not_empty("{}/{}".format(project_path , "ansible.cfg"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "env_vars/prod.yml"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "env_vars/preprod.yml"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "inventories/prod.ini"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "inventories/preprod.ini"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "inventories/prod.ini"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "requirements.txt"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "site.yml"))
  _check_file_exist_not_empty("{}/{}".format(project_path , "README.md"))

  try:
    for filename in os.listdir("{}/plays".format(project_path)):
      _check_file_exist_not_empty("{}/plays/{}".format(project_path , filename))

  except (AssertionError, OSError) as e:
    code_return = 2
    print e

def check_env_vars():
  global return_code
  global project_path
 
  try:
    for filename in os.listdir("{}/env_vars".format(project_path)):
      current_env_file = "{}/env_vars/{}".format(project_path, filename)
      env_vars = yaml_load(current_env_file)

      if env_vars is None:
        print RED_COLOR + "file {} doesn't have any variables".format(current_env_file) + RESET_COLOR
        return_code = 2
      else:
        for var_name in env_vars:
          var_name = var_name.replace("-","_")
          if re.match("^env_.*", var_name) is None:
            print RED_COLOR + "{} propertie dont respect the naming convention prefix env_ into {}".format(
            var_name, 
            current_env_file
            ) + RESET_COLOR
            return_code = 2
  except (IOError, KeyError, OSError) as e:
    print RED_COLOR + "folder {}/env_vars is empty.".format(project_path) + RESET_COLOR
    return_code = 2


def check_site_includes():
  global return_code
  global project_path

  try:
    site_yml = yaml_load("{}/site.yml".format(project_path))
    for line in site_yml:
      _check_file_exist_not_empty("{}/{}".format(project_path , line['include']))
      
  except (IOError, OSError):
    print RED_COLOR + "can't read file {}/site.yml".format(project_path) + RESET_COLOR
    return_code = 2
  except(KeyError, TypeError):
    print RED_COLOR + "can't read includes in file {}/site.yml, file is missformed.".format(project_path) + RESET_COLOR
    return_code = 2

def get_group_vars_path():
  global project_path
  global return_code

  if os.path.isdir("{}/group_vars".format(project_path)):
    return "group_vars"
  elif os.path.isdir("{}/inventories/group_vars".format(project_path)):
    return "inventories/group_vars"
  else:
     print RED_COLOR + "folder group_vars is missing, some tests can be achieved existing early..." + RESET_COLOR
     print RED_COLOR + "Project structure not good, Now i'am sad :(" + RESET_COLOR
     exit(0)


def check_group_vars(group_var_path):
  global project_path
  global return_code

  try:
    for group_folder in os.listdir("{}/{}".format(project_path, group_var_path)):
      try:
        for group_file in os.listdir("{}/{}/{}".format(project_path, group_var_path ,group_folder)):
          service_name = os.path.splitext(group_file)[0]
          service_name= service_name.replace("-","_")
          current_group_file = "{}/{}/{}/{}".format(project_path, group_var_path, group_folder, group_file)  
          _check_file_exist_not_empty(current_group_file)
          
          groups_vars = yaml_load(current_group_file)
  
          if groups_vars is None:
            print RED_COLOR + "file {} doesn't have any variables".format(current_group_file) + RESET_COLOR
            return_code = 2
          else:
            for group_name in groups_vars:
              if re.match("^{}_.*".format(service_name), group_name) is None:
                print RED_COLOR + "{} propertie dont respect the naming convention prefix {}_ into {}".format(
                group_name,
                service_name,
                current_group_file
                ) + RESET_COLOR
                return_code = 2
            
           
      except (IOError, KeyError, OSError) as e:
        print RED_COLOR + "folder {}/{} is empty .".format(project_path, group_var_path) + RESET_COLOR
        return_code = 2

  except (IOError, KeyError, OSError) as e:
    print RED_COLOR + "folder {}/group_vars is empty .".format(project_path, group_var_path) + RESET_COLOR
    return_code = 2


def check_roles():
  global return_code
  global project_path
  global script_path

  for role_folder in os.listdir("{}/roles".format(project_path)):
    if "." not in role_folder:
      print "\n\n\nCHECK ROLE: {}\n".format(role_folder)
      sys.stdout.flush()
      role_path = "{}/roles/{}".format(project_path, role_folder)
      code=call(["{}/role_check.py".format(script_path), "-p", role_path])
      sys.stdout.flush()
      if code is 2:
        return_code = 2

def main():
  global return_code
  return_code = 0
  check_args()
  print "CHECK Project Structure\n"
  sys.stdout.flush()

  check_default_files()
  check_site_includes()
  check_env_vars()
  group_var_path=get_group_vars_path()
  check_group_vars(group_var_path)

  if return_code is 0 :
    print GREEN_COLOR + "Project structure is fine, keep the good job :)" + RESET_COLOR
  else:
   print RED_COLOR + "Project structure not good, Now i'am sad :(" + RESET_COLOR

  check_roles()

  if return_code is 0 :
    print "\n"
    print GREEN_COLOR + "End of tests, everything is fine, keep the good job :)" + RESET_COLOR
  else:
   print "\n"
   print RED_COLOR + "End of tests, some tests failed, now i'am sad :(" + RESET_COLOR
  
  sys.exit(return_code)

if __name__ == '__main__':
  main()
