[out:json][timeout:25];

// Define search areas
area["name"="Boston"]["admin_level"="8"]->.boston;
area["name"="Brookline"]["admin_level"="8"]->.brookline;
area["name"="Cambridge"]["admin_level"="8"]->.cambridge;
area["name"="Somerville"]["admin_level"="8"]->.somerville;

// Search for pedestrian refuge islands (traffic islands) within these areas
(
  node["highway"="traffic_island"](area.boston);
  node["highway"="traffic_island"](area.brookline);
  node["highway"="traffic_island"](area.cambridge);
  node["highway"="traffic_island"](area.somerville);

  way["highway"="traffic_island"](area.boston);
  way["highway"="traffic_island"](area.brookline);
  way["highway"="traffic_island"](area.cambridge);
  way["highway"="traffic_island"](area.somerville);

  node["crossing:island"="yes"](area.boston);
  node["crossing:island"="yes"](area.brookline);
  node["crossing:island"="yes"](area.cambridge);
  node["crossing:island"="yes"](area.somerville);
);

out body;
>;
out skel qt;
