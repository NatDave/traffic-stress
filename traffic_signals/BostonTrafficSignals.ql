[out:json][timeout:25];
area[name="Boston"]->.searchArea;
(
  node["highway"="traffic_signals"](area.searchArea);
);
out body;
>;
out skel qt;
