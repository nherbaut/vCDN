set multiplot layout 1, 2 ;
set xlabel "number of transformations";
set ylabel "% of embded services"
set y2label "max delay to vcdn"
set y2tics 
set ytics nomirror
set y2range [0:10]
set yrange [0:10]
set title "Embeding the service on the Toy Topology";
plot  "simple.data" using 1:3 with lines axes x1y1 title "service embedding",  "simple.data" using 1:4 with lines axes x1y2 title "max delay"
set yrange [0:50]


set title "Embeding the service on Geant Topology";
plot  "geant.data" using 1:3 with lines axes x1y1 title "service embedding", "geant.data" using 1:4 with lines axes x1y2 title "max delay"
