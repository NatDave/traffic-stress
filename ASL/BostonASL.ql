[out:json];
(
  // Search for cycleways with advanced stop line (ASL) tag in the Boston area
  way["cycleway"="asl"](area["name"="Boston"]);
  
  // Search for nodes connected to junctions with ASL or bike box features in the Boston area
  node["cycleway"="asl"](area["name"="Boston"]);
);
out body;
>;
out skel qt;
