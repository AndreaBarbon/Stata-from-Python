%%px --local


import os; import pandas as pd; import numpy  as np
from pandas.tseries.offsets import *
import statsmodels.formula.api as smf


def winsorize(df, var, Q=0.01):
    Q1, Q2 = df[var].quantile(Q), df[var].quantile(1-Q)
    return np.where(df[var]<Q1, Q1, np.where(df[var]>Q2, Q2, df[var]))


### Stata regressions from python
#
################################################
## Dependencies for Stata: ivreg2 and reghdfe.
## Run the following in Stata to install them:
# ssc install reghdfe, replace
# ssc install ivreg2, replace
# ssc install ranktest, replace
################################################

# Change this (if needed) to point to the Stata app:
STATA_APP = "/Applications/Stata/StataMP.app/Contents/MacOS/StataMP"

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
    cmd = [STATA_APP, "do", do_file, *params]
    return subprocess.call(cmd)

def run_regression(do_file, spec="", timeout=60*60): 
    process = do_stata(do_file)
    wait_then_kill(process, timeout)

def gen_FEs_command(all_fes, reg_fes):

    bool_fes = ["Yes" if x in reg_fes else "-" for x in all_fes]
    name_fes = [x + " fixed effects" for x in all_fes]
    comm_fes = np.ravel([[x, y] for x,y in zip(name_fes, bool_fes)])
    comm_fes = "\"{0}\"".format("\", \"".join(comm_fes))
    return comm_fes

def replace_dict(string,dictionary):
    to_replace = [[x,y] for x,y in dictionary.items()]
    for rep in to_replace: string = string.replace(*rep)
    return string

def write_do_file_for_regression(reg, specs=None, do_file_name=None, test_only=False):
    
    if specs is None: specs = [reg]
        
    all_fes = []
    for spec in specs:
        if 'FEs' in spec.keys():
            for fe in spec['FEs']:
                if fe not in all_fes: all_fes.append(fe)
        
        for fe in reg['FEs']:
            if fe not in all_fes: all_fes.append(fe)
    
    s = """
    
    use {0}, clear
    set more off
    gen con = 1

    global SORT   = ""
    global NAME   = "{1}"
    global OUTREG = "outreg2 using $NAME.txt, asterisk(coef) r2 tstat nonotes dec(3) sortvar( $SORT )"
        
    """.format( reg['dataset'], reg['name'] )
    
    if test_only: s += """keep if _n < 1000"""
     
    for sp, spec in enumerate(specs):
        
        for key, value in spec.items(): reg[key] = spec[key]
            
        cl_text   = "-".join(reg['cluster'])
        cl_text   = replace_dict(cl_text ,rename_dict).title()
        
        desc_txt  = reg['desc_txt'] if 'desc_txt' in reg.keys() else ""
        desc_tit  = reg['desc_tit'] if 'desc_tit' in reg.keys() else "Description"

        add_text  = """ {0}, "SEs Clustered by", "{1}" """.format(gen_FEs_command(all_fes, reg['FEs']), cl_text)
        if desc_txt != "": add_text += """, "{0}", "{1}" """.format(desc_tit, desc_txt)
        add_text  = replace_dict(add_text,rename_dict).title()
        
        replace   = "replace" if sp == 0 else "append"
        condition = "if " + reg['condition'] if 'condition' in reg.keys() else ""
        if condition == "if " : condition = ""
        
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
    s += "\n exit, STATA clear \n"
    
    if do_file_name is None: do_file_name = reg['name']
    
    with open(do_file_name + ".do", 'w') as file: file.write(s);
        

def table_for_regression(reg, save_latex=False):
    
    print(reg['name'])
    tab = pd.read_table(reg['name'] + ".txt")
    tab = replace_dict(tab, reg['rename'])
    tab = tab.replace("VARIABLES","Dependent Variable").replace(np.nan,"")
    tab = tab.rename_axis({'Unnamed: 0':'index'}, axis=1).set_index("index")
    tab.index.name = None
    
    if save_latex: 
        tex_file_name = reg['name'] + '.tex'
        tab.to_latex(tex_file_name)
        with open(tex_file_name, 'r') as file : s = file.read()
        old =       "".join(['l']*(1+len(specs)))
        new = "l" + "".join(['c']*(len(specs)))
        s    = s.replace(old, new)
        with open(tex_file_name, 'w') as file: file.write(s)
            
    return tab