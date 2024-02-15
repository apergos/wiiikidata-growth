#!/usr/bin/bash

# Using the mediawiki action api, retrieve revision counts for
# wikidatawiki over time, and then produce a graph showing the
# growth using gnuplot.

gnuplotversion=$( gnuplot -V )
if [ $? -ne 0 ]; then
    echo "This script depends on gnuplot. Please make sure it is installed"
    echo "and in your executables path."
    exit 1
fi

DATE=$( date -u +'%b-%d-%Y' )
INFILE="wikidata-${DATE}.txt"
BASEDIR=$( pwd )
OUTPATH="${BASEDIR}/wikidata-${DATE}.png"

echo "OUTPATH is $OUTPATH"
echo "Starting the run; it will take a few minutes to retrieve all the data, no progress bar, sorry!"
python ./generate_rev_data.py --domain www.wikidata.org  >  "$INFILE"
echo "Done with retrieval, graphing"

# entries in the data file are of the format 2070000001 2024-02-06T00:32:12Z
if [ ! -f "$INFILE" ]; then
    echo "The data file was not written. Sorry about that, please poke around to fix."
    exit 1
fi

ENDRANGE=$( /usr/bin/tail -1 "$INFILE" | /usr/bin/cut -d ' ' -f 2 )
/usr/bin/cat gnuplot-cmds-wikidatawiki.txt.templ | /usr/bin/sed -e "s|INFILE|${INFILE}|g; s|OUTPATH|${OUTPATH}|g; s|ENDRANGE|${ENDRANGE}|g;" > gnuplot-cmds-wikidatawiki.txt

/usr/bin/cat gnuplot-cmds-wikidatawiki.txt | gnuplot
if [ ! -f "$OUTPATH" ]; then
    echo "The graph was not written. Sorry about that, please poke around to fix."
    exit 1
fi

echo "Done! Please collect your graph from ${BASEDIR}/wikidata-${DATE}.png"
exit 0
