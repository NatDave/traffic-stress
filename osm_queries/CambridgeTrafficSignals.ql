// Coordinates for bounding box (approximate) covering Cambridge, MA with 1 km circular buffer

[out:json][timeout:25];
(
  node["highway"="traffic_signals"](around(42.373611, -71.109733, 1000));
  node["crossing"](around(42.373611, -71.109733, 1000));
);
out body;
