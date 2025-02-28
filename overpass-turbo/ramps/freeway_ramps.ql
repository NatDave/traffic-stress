[out:json][timeout:60];

// Define search areas
area["name"="Boston"]["admin_level"="8"]->.boston;
area["name"="Brookline"]["admin_level"="8"]->.brookline;
area["name"="Cambridge"]["admin_level"="8"]->.cambridge;
area["name"="Somerville"]["admin_level"="8"]->.somerville;

// Get all motorway links (freeway ramps)
(
  way["highway"="motorway_link"](area.boston);
  way["highway"="motorway_link"](area.brookline);
  way["highway"="motorway_link"](area.cambridge);
  way["highway"="motorway_link"](area.somerville);
);

// Fetch all nodes belonging to the ways
(._; >;);

// Output JSON
out geom;
