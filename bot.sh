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
nRunCount=1
bRepeat=1
sFile=./config/*.json
sLogfile=./log/bot.log
bDry=0
while (( "$#" )); do
	sKey="$1"
	case $sKey in
		-c|--count)
			nRunCount="$2"
			shift
			;;
		-d|--dry)
			echo "Dry mode"
			bDry=1
			shift
			;;
		-r|--repeat)
			bRepeat="$2"
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
			echo "Run scrape.js one/multiple times."
			echo "Every run includes [-c] config files in reverse order of amounts processed. If [-r], after every run a new run is initiated."
			echo "  -c, --count     number of config files to process per run (0 = all; default: 1)"
			echo "  -d, --dry       enable dry mode where only config files are indexed"
			echo "  -f, --files     config files to process (default: ./config/*.json)"
			echo "  -l, --log       bot.sh log file path (default: ./log/bot.log)"
			echo "  -r, --repeat    boolean if bot.sh should run infinitely (default: 1)"
			echo ""
			echo "Examples"
			echo "bot.sh        same as bot.sh -c 1 -r 1"
			echo "              evaluate runtime count after every config file (-c 1)"
			echo "              run infinitely"
			echo "bot.sh -c 10  run infinitely, but evaluate runtime count only every 10 config files"
			echo "bot.sh -c 0   run infinitely, but do not evaluate runtime count"
			echo "bot.sh -r 0   run one (the least-run so far) config file once"
			exit 0
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
	((i++))
done

printf "%s config file(s) found\n" "${#aConf[@]}"
if [ $nRunCount -le 0 ]; then
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

# dry mode
if [ $bDry -eq 1 ]; then
	for k in "${!aConfCount[@]}"; do printf '%s\t%s\n' "${aConfCount[$k]}" "$k"; done | sort -g
fi

# start loop
while true; do
	# sort entries
	IFS=$'\n'
	set -f
	aConfCountKeysSorted=($(
		for k in "${!aConfCount[@]}"; do printf '%s\t%s\n' "${aConfCount[$k]}" "$k"; done | sort -g | sed $'s/.*\t//'
	  ))
	unset IFS
	
	# dry mode, 2
	if [ $bDry -eq 1 ]; then
		printf "If not dry, now running #%s\n" ${aConfCountKeysSorted[0]}
		exit 0
	fi
	
	# find the lowest x (nRunCount) entries and scrape.js them
	i=0
	while [ $i -lt $nRunCount ]; do
		if [ ${#aConfCountKeysSorted[@]} -gt $i ]; then
			sConf=${aConfCountKeysSorted[$i]}
			printf "Running #%s\n" "$sConf"
			casperjs ./scrape.js --uid=$sConf
			# log scrape.js call (first, add a new line; second, add the conf file name)
			sed -i -e '$a\' $sLogfile && echo "$sConf" >> $sLogfile
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
exit 0
