[out:json][timeout:50];
area[name="Boston"]->.searchArea;
(
  // Search for bike lanes, cycle tracks, bike paths, and related infrastructure
  way["cycleway"="lane"](area.searchArea);
  way["cycleway"="track"](area.searchArea);
  way["cycleway"="path"](area.searchArea);
  way["cycleway"="opposite_track"](area.searchArea);
  way["cycleway"="shared_lane"](area.searchArea);
  way["cycleway"="segregated"](area.searchArea);
  way["cycleway"="lane_and_track"](area.searchArea);
  way["cycleway"="bus_lane"](area.searchArea);
  way["cycleway"="shoulder"](area.searchArea);
  way["cycleway"="bus_only"](area.searchArea);
  way["highway"="cycleway"](area.searchArea);
  way["highway"="path"]["foot"="yes"](area.searchArea);
  
  // Shared paths for cyclists
  way["highway"="primary"]["cycleway"="lane"](area.searchArea);
  way["highway"="secondary"]["cycleway"="lane"](area.searchArea);
  way["highway"="tertiary"]["cycleway"="lane"](area.searchArea);
  way["highway"="residential"]["cycleway"="lane"](area.searchArea);
  way["highway"="living_street"]["cycleway"="lane"](area.searchArea);
  way["highway"="unclassified"]["cycleway"="lane"](area.searchArea);
  way["highway"="primary"]["cycleway"="track"](area.searchArea);
  way["highway"="secondary"]["cycleway"="track"](area.searchArea);
  way["highway"="tertiary"]["cycleway"="track"](area.searchArea);
  way["highway"="residential"]["cycleway"="track"](area.searchArea);
  way["highway"="living_street"]["cycleway"="track"](area.searchArea);
  way["highway"="unclassified"]["cycleway"="track"](area.searchArea);
);
out body;
>;
out skel qt;
