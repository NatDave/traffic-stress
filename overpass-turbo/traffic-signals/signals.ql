[out:json][timeout:25];

// Define search areas for each city using area references by administrative boundaries
area["name"="Boston"]["admin_level"="8"]->.boston;
area["name"="Brookline"]["admin_level"="8"]->.brookline;
area["name"="Cambridge"]["admin_level"="8"]->.cambridge;
area["name"="Somerville"]["admin_level"="8"]->.somerville;

// Find nodes with "traffic_signals" in the combined search areas
(
  node["highway"="traffic_signals"](area.boston);
  node["highway"="traffic_signals"](area.brookline);
  node["highway"="traffic_signals"](area.cambridge);
  node["highway"="traffic_signals"](area.somerville);
);

out body;
>;
out skel qt;
