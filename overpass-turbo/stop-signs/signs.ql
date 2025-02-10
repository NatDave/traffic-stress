[out:json][timeout:25];

// Define search areas for each city using area references by administrative boundaries
area["name"="Boston"]["admin_level"="8"]->.boston;
area["name"="Brookline"]["admin_level"="8"]->.brookline;
area["name"="Cambridge"]["admin_level"="8"]->.cambridge;
area["name"="Somerville"]["admin_level"="8"]->.somerville;

// Find nodes with "highway=stop" in the combined search areas
(
  node["highway"="stop"](area.boston);
  node["highway"="stop"](area.brookline);
  node["highway"="stop"](area.cambridge);
  node["highway"="stop"](area.somerville);
);

out body;
>;
out skel qt;
