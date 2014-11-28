#!/bin/bash

site=`dnsdomainname`
if [ -e $fwk/Configuration/site/$site/environment.sh ]; then
    source $fwk/Configuration/site/$site/environment.sh 
else
    echo "Domain name $site not available in the list of supported sites."
    echo "Change site or add the proper configuration in Configuration/site/$dnsdomainname"
fi