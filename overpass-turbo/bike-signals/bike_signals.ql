[out:json][timeout:25];

// Define search areas for each city
area["name"="Boston"]["admin_level"="8"]->.boston;
area["name"="Brookline"]["admin_level"="8"]->.brookline;
area["name"="Cambridge"]["admin_level"="8"]->.cambridge;
area["name"="Somerville"]["admin_level"="8"]->.somerville;

// Search for bike-specific traffic signals within these areas
(
  node["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.boston);
  node["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.brookline);
  node["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.cambridge);
  node["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.somerville);

  way["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.boston);
  way["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.brookline);
  way["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.cambridge);
  way["highway"="traffic_signals"]["traffic_signals:bicycle"="yes"](area.somerville);
);

out body;
>;
out skel qt;
