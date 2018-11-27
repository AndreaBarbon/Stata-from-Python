
    
cd "/Users/abramo/Repos/Stata from Python/Regressions/"
use approval_data, clear
set more off
gen con = 1

global SORT   = ""
global NAME   = "mixed"
global OUTREG = "outreg2 using $NAME.txt, asterisk(coef) r2 tstat nonotes dec(3) sortvar( $SORT )"
        

reghdfe approve adults , cluster( startdate company ) absorb( company startdate )
$OUTREG replace addtext( "Company Fixed Effects", "Yes", "Date Fixed Effects", "Yes", "Ses Clustered By", "Date-Company" )


reghdfe disapprove adults , cluster( startdate company ) absorb( company startdate )
$OUTREG append addtext( "Company Fixed Effects", "Yes", "Date Fixed Effects", "Yes", "Ses Clustered By", "Date-Company" )


ivreg2  approve adults if pollster=="Gallup", cluster( startdate )
$OUTREG append addtext( "Company Fixed Effects", "-", "Date Fixed Effects", "-", "Ses Clustered By", "Date" , "Pollster", "Only Gallup" )


reghdfe approve adults if pollster!="Gallup", cluster( startdate company ) absorb( startdate company )
$OUTREG append addtext( "Company Fixed Effects", "Yes", "Date Fixed Effects", "Yes", "Ses Clustered By", "Date-Company" , "Pollster", "All But Gallup" )


exit, STATA clear 
