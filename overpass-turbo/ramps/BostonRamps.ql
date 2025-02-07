[out:json][timeout:25];
area["name"="Boston"]["boundary"="administrative"]->.searchArea;
(
  way["highway"="motorway_link"](area.searchArea);
);
out body;
>;
out skel qt;
