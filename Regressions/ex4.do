
    
cd "/Users/abramo/Repos/Stata from Python/Regressions/"
use ex4, clear
set more off
gen con = 1

global SORT   = ""
global NAME   = "ex4"
global OUTREG = "outreg2 using $NAME.txt, asterisk(coef) r2 tstat nonotes dec(3) sortvar( $SORT )"
        
gen adults_proxy = . 
replace adults_proxy = adults

ivreg2  approve adults_proxy , cluster( startdate company )
$OUTREG replace addtext(  "Ses Clustered By", "Date-Company" , "Adult Proxy", "Standard" , "Note", "Boh" )

drop adults_proxy 
gen adults_proxy = . 
replace adults_proxy = adults_win

ivreg2  approve adults_proxy , cluster( startdate company )
$OUTREG append addtext(  "Ses Clustered By", "Date-Company" , "Adult Proxy", "Winsorized" , "Note", "Jesse" )

drop adults_proxy 

exit, STATA clear 
