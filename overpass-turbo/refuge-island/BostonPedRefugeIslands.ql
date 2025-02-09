[out:json][timeout:25];
area["name"="Boston"]["boundary"="administrative"]->.searchArea;
(
  node["highway"="crossing"]["crossing:island"="yes"](area.searchArea);
  way["highway"="footway"]["footway"="traffic_island"](area.searchArea);
);
out body;
