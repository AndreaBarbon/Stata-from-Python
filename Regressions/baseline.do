
    
cd "/Users/abramo/Repos/Stata from Python/Regressions/"
use approval_data, clear
set more off
gen con = 1

global SORT   = ""
global NAME   = "baseline"
global OUTREG = "outreg2 using $NAME.txt, asterisk(coef) r2 tstat nonotes dec(3) sortvar( $SORT )"
        

ivreg2  approve adults , cluster( startdate company )
$OUTREG replace addtext( "Company Fixed Effects", "-", "Date Fixed Effects", "-", "Ses Clustered By", "Date-Company" )


reghdfe approve adults , cluster( startdate company ) absorb( company )
$OUTREG append addtext( "Company Fixed Effects", "Yes", "Date Fixed Effects", "-", "Ses Clustered By", "Date-Company" )


reghdfe approve adults , cluster( startdate company ) absorb( startdate )
$OUTREG append addtext( "Company Fixed Effects", "-", "Date Fixed Effects", "Yes", "Ses Clustered By", "Date-Company" )


reghdfe approve adults , cluster( startdate company ) absorb( company startdate )
$OUTREG append addtext( "Company Fixed Effects", "Yes", "Date Fixed Effects", "Yes", "Ses Clustered By", "Date-Company" )


exit, STATA clear 
