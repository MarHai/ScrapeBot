#!/bin/bash

#chkconfig: 35 80 05
#description: ScrapeBot

#
# ScrapeBot/bot.sh
#
# Iterates over config files, selects some of them, and runs them.
# Moreover, keeps track of a +/- equal distribution of config usages.
#
# TOC:
#   interpret command line args
#   collect all config files from ./config/
#   read ./log/bot.log and count runs per config file
#   start loop and ...
#    sort ascending
#    scrape.js config files
#    log scrape.js call
#
# (c) 2015
# Mario Haim <haim@ifkw.lmu.de>
# LMU Munich
#

# interpret command line args
nRunCount=-1
bRepeat=1
sFile=./config/*.json
sLogfile=./log/bot.log
while [ $# -gt 1 ]; do
	sKey="$1"
	case $sKey in
		-c|--count)
			nRunCount="$2"
			shift
			;;
		-r|--repeat)
			bRepeat=1
			shift
			;;
		-f|--files)
			sFile="$2"
			shift
			;;
		-l|--log)
			sLogfile="$2"
			shift
			;;
		-h|--help)
			echo "Usage: bot.sh [OPTION]..."
			echo "Run scrape.js one/multiple times"
			echo ""
			echo "  -c, --count     number of config files to process (default: -1/all)"
			echo "  -f, --files     config files to process (default: ./config/*.json)"
			echo "  -l, --log       bot.sh log file path (default: ./log/bot.log)"
			echo "  -r, --repeat    boolean if bot.sh should run infinitely (default: 1)"
			shift
			;;
		*)
			# unknown option
			;;
	esac
	shift
done

echo "Running $nRunCount (-1 = all) configuration files with infinite mode set to $bRepeat"

# collect config files and set each run counter to 0
i=0
aConf=()
declare -A aConfCount
for f in $sFile; do
	aConf[$i]=$(echo $f | rev | cut -d '/' -f 1 | rev | cut -d '.' -f 1)
	aConfCount[${aConf[$i]}]=0
done

printf "%s config file(s) found\n" "${#aConf[@]}"
if [ $nRunCount -eq -1 ]; then
	nRunCount=${#aConf[@]}
fi

# run through log and count scrape.js calls per config file
if [ -e "$sLogfile" ]; then
	while read sLog; do
		aConfCount[$sLog]=$((${aConfCount[$sLog]} + 1))
	done < $sLogfile
else
	echo "No log file found."
fi

# start loop
while true; do
	# sort entries
	IFS=$'\n'
	set -f
	aConfCountKeysSortedDesc=($(
		for k in "${!aConfCount[@]}"; do printf '%s\t%s\n' "${aConfCount[$k]}" "$k"; done | sort -r | sed $'s/.*\t//'
	  ))
	unset IFS

	# find the lowest x (nRunCount) entries and scrape.js them
	i=0
	while [ $i -lt $nRunCount ]; do
		if [ ${#aConfCountKeysSortedDesc[@]} -gt $i ]; then
			sConf=${aConfCountKeysSortedDesc[$i]}
			printf "Running #%s\n" "$sConf"
			casperjs ./scrape.js --uid=$sConf
			# log scrape.js call
			echo "$sConf" >> $sLogfile
			aConfCount[$sConf]=$((${aConfCount[$sConf]} + 1))
		fi
		((i++))
	done
	
	# if repeat was set to 0, exit while
	if [ $bRepeat -eq 0 ]; then
		break
	fi
done

echo "Bot done"
