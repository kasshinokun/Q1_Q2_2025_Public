class DataObject:
    def __init__(self, row_data):
        self.crash_date = str(row_data[0])  # String
        self.traffic_control_device = str(row_data[1])  # String
        self.weather_condition = str(row_data[2])  # String
        self.lighting_condition = str(row_data[3])  # String
        self.first_crash_type = str(row_data[4])  # String
        self.trafficway_type = str(row_data[5])  # String
        self.alignment = str(row_data[6])  # String
        self.roadway_surface_cond = str(row_data[7])  # String
        self.road_defect = str(row_data[8])  # String
        self.crash_type = str(row_data[9])  # String
        self.intersection_related_i = str(row_data[10])  # String (Y/N)
        self.damage = str(row_data[11])  # String
        self.prim_contributory_cause = str(row_data[12])  # String
        self.num_units = int(row_data[13])  # Integer
        self.most_severe_injury = str(row_data[14])  # String
        self.injuries_total = float(row_data[15])  # Float
        self.injuries_fatal = float(row_data[16])  # Float
        self.injuries_incapacitating = float(row_data[17])  # Float
        self.injuries_non_incapacitating = float(row_data[18])  # Float
        self.injuries_reported_not_evident = float(row_data[19])  # Float
        self.injuries_no_indication = float(row_data[20])  # Float
        self.crash_hour = int(row_data[21])  # Integer
        self.crash_day_of_week = int(row_data[22])  # Integer
        self.crash_month = int(row_data[23])  # Integer

    def __str__(self):
        return (f"DataObject(crash_date={self.crash_date}, "
                f"traffic_control_device={self.traffic_control_device}, "
                f"weather_condition={self.weather_condition}, ...)")