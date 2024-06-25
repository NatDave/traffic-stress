class Mixin:
    """
    Mixin class providing the xLTS calculation for crossing stress levels.
    """

    def xLTS_calc(self, control, pocket_trigger, crossing_distance,
                  two_stage, link_type, speed_limit, crossing_island,
                  adt, num_lanes, visibility_limit, circular_sensitivity,
                  ramp_trigger, bike_signal, sas_bike, rt_volume, bike_advance):
        """
        Calculate the Level of Traffic Stress (LTS) for a crossing.

        :param control: Type of traffic control (e.g., 'Stop4', 'Signal')
        :param pocket_trigger: Indicator for bike lane pocket
        :param crossing_distance: Distance to nearest signal or stop sign
        :param two_stage: Indicator for two-stage crossing
        :param link_type: Type of link (e.g., 'Road', 'Trail')
        :param speed_limit: Speed limit of the road
        :param crossing_island: Indicator for crossing island presence
        :param adt: Average daily traffic
        :param num_lanes: Number of lanes
        :param visibility_limit: Visibility limit
        :param circular_sensitivity: Sensitivity for circular crossings
        :param ramp_trigger: Trigger for ramp conflict
        :param bike_signal: Indicator for bike signal presence
        :param sas_bike: Indicator for SAS bike
        :param rt_volume: Right-turn volume
        :param bike_advance: Indicator for bike advance
        :return: Calculated LTS value
        """
        # Calculate the number of lanes to be crossed
        num_lanes_crossed = 2 * num_lanes if circular_sensitivity == 0 else num_lanes

        # Initialize LTS to 1
        lts = 1

        # Evaluate LTS based on control type
        if control == 'Stop4':
            lts = 1
        elif control == 'Signal':
            lts = self._calculate_signal_lts(lts, bike_signal, sas_bike, rt_volume, crossing_distance, two_stage, pocket_trigger, bike_advance)
        else:
            lts = self._calculate_unsignalized_lts(lts, link_type, num_lanes_crossed, adt, speed_limit, crossing_island)

        # Adjust LTS based on visibility limit and ramp trigger
        lts = max(2, lts) if visibility_limit > 0 else lts
        lts = max(lts, ramp_trigger)

        return lts

    def _calculate_signal_lts(self, lts, bike_signal, sas_bike, rt_volume, crossing_distance, two_stage, pocket_trigger, bike_advance):
        """
        Calculate LTS for signalized crossings.
        """
        if bike_signal == 0:
            if (sas_bike > 0 or bike_advance > 0) and rt_volume > 240:
                lts = 2
            elif rt_volume > 120:
                lts = 2

        if crossing_distance > 30 or two_stage > 0 or pocket_trigger == 2:
            lts = 2
        elif pocket_trigger == 3:
            lts = 3

        return lts

    def _calculate_unsignalized_lts(self, lts, link_type, num_lanes_crossed, adt, speed_limit, crossing_island):
        """
        Calculate LTS for unsignalized crossings.
        """
        if link_type != 'Road':
            lts = self._calculate_trail_crossing_lts(lts, num_lanes_crossed, adt, speed_limit, crossing_island)
        else:
            lts = self.lts_b(speed_limit, crossing_island, adt, num_lanes_crossed)

        return lts

    def _calculate_trail_crossing_lts(self, lts, num_lanes_crossed, adt, speed_limit, crossing_island):
        """
        Calculate LTS for trail crossings.
        """