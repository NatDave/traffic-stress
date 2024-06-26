class Mixin:
    """
    Mixin class providing the xLTS calculation for crossing stress levels.
    """

    def xLTS_calc(self, control, pocket_trigger, crossing_distance_sig, two_stage, link_type,
                  speed_limit, crossing_island, adt, num_lanes, visibility_limit,
                  circular_sensitivity, ramp_trigger, bike_signal, sas_bike, rt_volume, avanc_flech):
        """
        Calculate the Level of Traffic Stress for a crossing (xLTS)

        :param control: Type of traffic control (e.g., 'Stop4', 'Signal')
        :param pocket_trigger: Indicator for bike lane pocket
        :param crossing_distance_sig: crossing distance at a signalized intersectionl.
        :param two_stage: Indicator for two-stage crossing
        :param link_type: Type of link (e.g., 'Road', 'Trail')
        :param speed_limit: Speed limit of the road
        :param crossing_island: Indicator for crossing island presence
        :param adt: Average daily traffic
        :param num_lanes: Number of lanes
        :param visibility_limit: Visibility limitation (blind entry)
        :param circular_sensitivity: Sensitivity for circular crossings
        :param ramp_trigger: Trigger for ramp conflict
        :param bike_signal: Indicator for bike signal presence
        :param sas_bike: Indicator for SAS bike
        :param rt_volume: Right-turn volume
        :param avanc_flech: Indicator for through signal (cars) presence
        """
        # Calculate the number of lanes to be crossed
        num_lanes_crossed = 2 * num_lanes if circular_sensitivity == 0 else num_lanes

        # Initialize xLTS to 1
        xlts = 1

        # Evaluate xLTS based on control type
        if control == 'Stop4':
            xlts = 1
        elif control == 'Signal':
            xlts = self._calculate_signal_xlts(xlts, bike_signal, sas_bike, rt_volume, crossing_distance_sig, two_stage, pocket_trigger, avanc_flech)
        else:
            xlts = self._calculate_unsignalized_xlts(xlts, link_type, num_lanes_crossed, adt, speed_limit, crossing_island)

        # Adjust xLTS based on visibility limit and ramp trigger
        xlts = max(2, xlts) if visibility_limit > 0 else xlts
        xlts = max(xlts, ramp_trigger)

        return xlts

    def _calculate_signal_xlts(self, xlts, bike_signal, sas_bike, rt_volume, crossing_distance_sig, two_stage, pocket_trigger, avanc_flech):
        """
        Calculate xLTS for signalized crossings.
        """
        if bike_signal == 0:
            if (sas_bike > 0 or avanc_flech > 0) and rt_volume > 240:
                xlts = 2
            elif rt_volume > 120:
                xlts = 2

        if crossing_distance_sig > 30 or two_stage > 0 or pocket_trigger == 2:
            xlts = 2
        elif pocket_trigger == 3:
            xlts = 3

        return xlts

    def _calculate_unsignalized_xlts(self, xlts, link_type, num_lanes_crossed, adt, speed_limit, crossing_island):
        """
        Calculate xLTS for unsignalized crossings.
        """
        if link_type != 'Road': # accounting for standalone trails
            xlts = self._calculate_trail_crossing_xlts(xlts, num_lanes_crossed, adt, speed_limit, crossing_island)
        else:
            xlts = self.calc_xLTS_static_method(speed_limit, crossing_island, adt, num_lanes_crossed)

        return xlts

    def _calculate_trail_crossing_xlts(self, xlts, num_lanes_crossed, adt, speed_limit, crossing_island):
        """
        Calculate xLTS for trail crossings.
        """
        if num_lanes_crossed == 1:
            if adt <= 8000:
                xlts = 1 if speed_limit <= 62 else self.calc_xLTS_static_method(speed_limit, crossing_island, adt, num_lanes_crossed)
            else:
                xlts = 1 if speed_limit <= 46 and crossing_island > 0 else self.calc_xLTS_static_method(speed_limit, crossing_island, adt, num_lanes_crossed)
        else:
            xlts = self.calc_xLTS_static_method(speed_limit, crossing_island, adt, num_lanes_crossed)

        return xlts

@staticmethod
def calc_xLTS_static_method(speed_limit, crossing_island, adt, num_lanes_crossed):
    """
    Calculate the baseline xLTS for a crossing
    """

    if speed_limit <= 62:  # 85th %ile speed on the road being crossed <= 62 km/h
        if 0 < crossing_island < 1.8:
            if adt <= 6000:
                return 1
            elif adt <= 24000:
                return 2
            else:
                return 3
        elif crossing_island >= 1.8:
            if adt <= 12000:
                return 1
            elif adt <= 24000:
                return 2
            else:
                return 3
        elif num_lanes_crossed in [1, 2, 3]:
            if adt <= 9000:
                return 1
            elif adt <= 17000:
                return 2
            else:
                return 3
        elif num_lanes_crossed >= 4:
            if adt <= 6000:
                return 1
            elif adt <= 12000:
                return 2
            elif adt <= 19000:
                return 3
            else:
                return 4
        else:
            return 1001

    else:  # 85th %ile speed on the road being crossed > 62 km/h
        if 0 < crossing_island < 1.8:
            if adt <= 17000:
                return 2
            else:
                return 3
        elif crossing_island >= 1.8:
            if adt <= 8000:
                return 1
            elif adt <= 17000:
                return 2
            else:
                return 3
        elif num_lanes_crossed in [1, 2, 3]:
            if adt <= 6000:
                return 1
            elif adt <= 12000:
                return 2
            elif adt <= 18000:
                return 3
            else:
                return 4
        elif num_lanes_crossed >= 4:
            if adt <= 10000:
                return 2
            elif adt <= 14000:
                return 3
            else:
                return 4
        else:
            return 1002