set xlabel "number of transformations";
set ylabel "% of embded services"
set ytics nomirror
set yrange [0:20]

set title "Embeding the service on Geant Topology";
plot  "geant.data" using 1:2 with lines axes x1y1 title "service embedding"
