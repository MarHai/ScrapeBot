#!/bin/bash

#
# ScrapeBot/bot.sh
#
# Iterates over config files, selects some of them, and runs them.
# Moreover, keeps track of a +/- equal distribution of config usages.
#
# TOC:
#   collect all config files from ./config/
#   read ./log/bot.log and count runs per config file
#   sort ascending
#   scrape.js the first 5 config files
#
# (c) 2015
# Mario Haim <haim@ifkw.lmu.de>
# LMU Munich
#

# collect config files and set each run counter to 0
i=0
aConf=()
declare -A aConfCount
for f in ./config/*.json; do
	aConf[$i]=$(echo $f | rev | cut -d '/' -f 1 | rev | cut -d '.' -f 1)
	aConfCount[${aConf[$i]}]=0
done

printf "%s config file(s) found\n" "${#aConf[@]}"

# run through log and count scrape.js calls per config file
sLogfile=./log/bot.log
if [ -e "$sLogfile" ]; then
	while read sLog; do
		aConfCount[$sLog]=$((${aConfCount[$sLog]} + 1))
	done < $sLogfile
else
	echo "No log file found."
fi

# sort entries
IFS=$'\n'
set -f
aConfCountKeysSortedDesc=($(
    for k in "${!aConfCount[@]}"; do printf '%s\t%s\n' "${aConfCount[$k]}" "$k"; done | sort -r | sed $'s/.*\t//'
  ))
unset IFS

# find the lowest 5 entries and scrape.js them
i=0
while [ $i -lt 5 ]; do
	if [ ${#aConfCountKeysSortedDesc[@]} -gt $i ]; then
		sConf=${aConfCountKeysSortedDesc[$i]}
		printf "Running #%s\n" "$sConf"
		casperjs ./scrape.js --uid=$sConf
		echo "$sConf" >> $sLogfile
	fi
	((i++))
done

echo "Bot done"
