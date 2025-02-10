[out:json][timeout:25];
area["name"="Boston"]["boundary"="administrative"]->.searchArea;
(
  node["highway"="stop"](area.searchArea);
);
out body;
