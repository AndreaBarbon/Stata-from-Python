### Imports
import pandas as pd; import numpy  as np
import os;

### Stata regressions from python
#
################################################
## Dependencies for Stata: ivreg2 and reghdfe.
## Run the following in Stata to install them:
# ssc install reghdfe, replace
# ssc install ivreg2, replace
# ssc install ranktest, replace
################################################


### CONFIGURATION ##############################
#
# Change this (if needed) to point to the Stata app:
# Mac example:
STATA_APP = "/Applications/Stata/StataMP.app/Contents/MacOS/StataMP"
WINDOWS   = False
#
# Windows example:
# STATA_APP = "C:\Program Files (x86)\Stata14\StataMP-64.exe"
# WINDOWS   = True
#
# Set up the folder where outputs will be placed.
# CAUTION: the folder name cannot contain white spaces
TARGET_FOLDER = "Regressions"
# Leave it `None` if you want everyhting to stay in the main working directory
# If you change it, remember to save your .dta files in that folder
#
################################################

if TARGET_FOLDER is None: TARGET_FOLDER = os.getcwd()
slash = "\\" if WINDOWS else "/"
    
target = TARGET_FOLDER if (TARGET_FOLDER.endswith("/") | (TARGET_FOLDER=="")) else TARGET_FOLDER + slash
if not target.startswith(os.getcwd()): target = os.getcwd() + slash + target

#print(target)


################################################
# Functions

def wait_then_kill(process, timeout=60*60):
    if process == 0: return
    try:
        process.wait(timeout=timeout)
    except Exception as e:
        print(e)
        process.kill()    

def do_stata(do_file, *params):
        
    ## Launch a do-file, given the fullpath to the do-file
    ## and a list of parameters.
    import subprocess
    
    launcher = """
    cd "{0}"
    do  {1}
    """.format(target, do_file)
    with open("launcher.do", 'w') as file: file.write(launcher);
        
    cmd = [STATA_APP, "do", 'launcher', *params]
    return subprocess.call(cmd)

def run_regression(do_file, spec="", timeout=60*60):
    
    try: do_file = do_file['name']
    except: pass
    
    process = do_stata(do_file)
    wait_then_kill(process, timeout)

def gen_FEs_command(all_fes, reg_fes):

    try:
        x = all_fes[0]
    except:
        return ""
    
    bool_fes = ["Yes" if x in reg_fes else "-" for x in all_fes]
    name_fes = [x + " fixed effects" for x in all_fes]
    comm_fes = np.ravel([[x, y] for x,y in zip(name_fes, bool_fes)])
    comm_fes = "\"{0}\"".format("\", \"".join(comm_fes))
    return comm_fes + ","

def replace_dict(string,dictionary):
    to_replace = [[x,y] for x,y in dictionary.items()]
    for rep in to_replace: string = string.replace(*rep)
    return string

def write_do_file_for_regression(reg, specs=None, do_file_name=None, test_only=False):
    

    to_turn_into_list = ['exp_vars', 'cluster', 'FEs', 'sort']
    for key in to_turn_into_list:
        try   : reg[key] = reg[key].split(" ")
        except: pass


    rename_dict = reg['rename']
    
    if specs is None: specs = [reg]
        
    if 'sort' in reg.keys(): sort = " ".join(reg['sort'])

    all_fes = []
    for spec in specs:
        if 'FEs' in spec.keys():
            for fe in spec['FEs']:
                if fe not in all_fes: all_fes.append(fe)
        
        for fe in reg['FEs']:
            if fe not in all_fes: all_fes.append(fe)
    
    s = """
    
cd "{0}"
use {1}, clear
set more off
gen con = 1

global SORT   = "{2}"
global NAME   = "{3}"
global OUTREG = "outreg2 using $NAME.txt, asterisk(coef) r2 tstat nonotes dec(3) sortvar( $SORT )"
        
""".format( target, reg['dataset'], sort, reg['name'] )
    
    if test_only: s += """keep if _n < 10000
    
"""
     
    for sp, spec in enumerate(specs):
        
        for key, value in spec.items(): reg[key] = spec[key]
            
        cl_text   = "-".join(reg['cluster'])
        if cl_text == "": cl_text="-"
        cl_text   = replace_dict(cl_text ,rename_dict).title()
        
        desc_txt  = reg['desc_txt'] if 'desc_txt' in reg.keys() else ""
        desc_tit  = reg['desc_tit'] if 'desc_tit' in reg.keys() else "Description"

        add_text  = """ {0} "SEs Clustered by", "{1}" """.format(gen_FEs_command(all_fes, reg['FEs']), cl_text)
        if desc_txt != "": add_text += """, "{0}", "{1}" """.format(desc_tit, desc_txt)
        add_text  = replace_dict(add_text,rename_dict).title()
        
        replace   = "replace" if sp == 0 else "append"
        condition = "if " + reg['condition'] if 'condition' in reg.keys() else ""
        if condition == "if " : condition = ""

        if 'rename_exp_vars' in reg.keys(): 
            for old_var, new_var in reg['rename_exp_vars'].items():
                s += """gen {0} = . \nreplace {0} = {1}""".format(new_var, old_var)
                reg['exp_vars'] = [x.replace(old_var, new_var) for x in reg['exp_vars']]

        params   = ( reg['dep_var'],
                " ".join(reg['exp_vars']),
                condition,            
                " ".join(reg['cluster']),
                " ".join(reg['FEs']),
                replace,
                add_text,
            )
                
        if len(reg['FEs']) == 0: # Univariate Regression

            s += """
ivreg2  {0} {1} {2}, cluster( {3} )
$OUTREG {5} addtext({6})

""".format(*params)

        else: # Regression with FEs

            s += """
reghdfe {0} {1} {2}, cluster( {3} ) absorb( {4} )
$OUTREG {5} addtext({6})

""".format(*params)

        if 'rename_exp_vars' in reg.keys(): s += """drop {0} \n""".format(new_var)


    s += "\nexit, STATA clear \n"
    
    if do_file_name is None: do_file_name = reg['name']
    
    with open(target + do_file_name + ".do", 'w') as file: file.write(s);
        
def table_for_regression(reg, save_latex=False):
    
    print(reg['name'])
    tab = pd.read_table(target + reg['name'] + ".txt")
    tab = replace_dict(tab, reg['rename'])
    tab = tab.replace("VARIABLES","Dependent Variable").replace(np.nan,"")
    tab = tab.rename_axis({'Unnamed: 0':'index'}, axis=1).set_index("index")
    tab.index.name = None
    n_specs = len(tab.columns)
    
    if save_latex: 
        tex_file_name = target + reg['name'] + '.tex'
        tab.to_latex(tex_file_name)
        with open(tex_file_name, 'r') as file : s = file.read()
        old =       "".join(['l']*(1+n_specs))
        new = "l" + "".join(['c']*(n_specs))
        s    = s.replace(old, new)
        with open(tex_file_name, 'w') as file: file.write(s)
            
    return tab

def winsorize(df, var, Q=0.01):
    Q1, Q2 = df[var].quantile(Q), df[var].quantile(1-Q)
    return np.where(df[var]<Q1, Q1, np.where(df[var]>Q2, Q2, df[var]))