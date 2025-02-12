[out:json][timeout:25];

// Define search areas for each city using administrative boundaries
area["name"="Boston"]["admin_level"="8"]->.boston;
area["name"="Brookline"]["admin_level"="8"]->.brookline;
area["name"="Cambridge"]["admin_level"="8"]->.cambridge;
area["name"="Somerville"]["admin_level"="8"]->.somerville;

// Search for bike boxes (Advanced Stop Lines) within these areas
(
  node["cycleway"="asl"](area.boston);
  node["cycleway"="asl"](area.brookline);
  node["cycleway"="asl"](area.cambridge);
  node["cycleway"="asl"](area.somerville);
  
  way["cycleway"="asl"](area.boston);
  way["cycleway"="asl"](area.brookline);
  way["cycleway"="asl"](area.cambridge);
  way["cycleway"="asl"](area.somerville);
  
  node["bicycle"="designated"]["highway"="stop"](area.boston);
  node["bicycle"="designated"]["highway"="stop"](area.brookline);
  node["bicycle"="designated"]["highway"="stop"](area.cambridge);
  node["bicycle"="designated"]["highway"="stop"](area.somerville);
);

out body;
>;
out skel qt;
