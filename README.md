This is a one-off that doesn't really deserve a repo. But it needs to be somewhere that
other folks can find it, run one command, and collect the resulting graph.

It just generates a little graph showing the growth of Wikidata over time. A few people
need this once in a awhile. If you came across this repo by accident, you don't need
this, lucky you.

To use:

Be on a linux system with standard utils in the usual places (cat, sed, etc)
Have **python(3)** and **gnuplot** installed and in your path
Run the command
  **bash ./generate-graph.sh**
Be patient, it has to ask the servers for a lot of revision counts. Wikidata is BIG.
Collect the graph from where the script tells you, once it is done.

