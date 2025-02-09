[out:json][timeout:25];
area[name="Boston"]->.searchArea;
(
  // Search for bike-specific signals
  node["cycleway"="signal"](area.searchArea);
);
out body;
>;
out skel qt;
