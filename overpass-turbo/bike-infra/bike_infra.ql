// Query to get bike infrastructure (bike lanes, cycle tracks, bike paths, etc.) for Boston, Cambridge, Brookline, and Somerville

[out:json][timeout:25];
// Define the area: Boston, Cambridge, Brookline, Somerville
{{geocodeArea:Boston}}->.bostonArea;
{{geocodeArea:Cambridge}}->.cambridgeArea;
{{geocodeArea:Brookline}}->.brooklineArea;
{{geocodeArea:Somerville}}->.somervilleArea;

(
  way["cycleway"~"lane|track|path|segregated|opposite_lane|shared_lane|designated|construction|both_ways"](area.bostonArea);
  way["cycleway"~"lane|track|path|segregated|opposite_lane|shared_lane|designated|construction|both_ways"](area.cambridgeArea);
  way["cycleway"~"lane|track|path|segregated|opposite_lane|shared_lane|designated|construction|both_ways"](area.brooklineArea);
  way["cycleway"~"lane|track|path|segregated|opposite_lane|shared_lane|designated|construction|both_ways"](area.somervilleArea);
);

// Include nodes for way geometry
(._;>;);
out body;
