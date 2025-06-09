st.subheader("Required Accident Details (*)")
        cols_req = st.columns(2)
        
        with cols_req[0]:
            crash_date = st.date_input(
                "Crash Date*",
                value=date.today(),
                help="Date of the accident (YYYY-MM-DD)",
                key="add_crash_date"
            )
        with cols_req[1]:
            crash_type = st.text_input(
                "Crash Type*",
                help="Main type of collision (e.g., Rear-End, Head-On, Side-Swipe, Rollover)",
                key="add_crash_type"
            )
        
        cols_units_inj = st.columns(2)
        with cols_units_inj[0]:
            num_units = st.number_input(
                "Number of Units Involved*",
                min_value=0,
                max_value=999,
                value=1,
                step=1,
                help="Total number of vehicles/units involved in the crash.",
                key="add_num_units"
            )
        with cols_units_inj[1]:
            injuries_total = st.number_input(
                "Total Injuries*",
                min_value=0.0,
                value=0.0,
                step=0.1,
                help="Total count of all injuries (fatal, incapacitating, etc.).",
                key="add_injuries_total"
            )

        st.subheader("Optional Details")
        cols1 = st.columns(3)
        with cols1[0]:
            traffic_control_device = st.selectbox(
                "Traffic Control Device",
                ["UNKNOWN", "TRAFFIC SIGNAL", "STOP SIGN", "YIELD SIGN", "NONE", "OTHER"],
                index=0, key="add_tcd"
            )
            weather_condition = st.selectbox(
                "Weather Condition",
                ["UNKNOWN", "CLEAR", "RAIN", "SNOW", "FOG", "SEVERE CROSSWINDS", "SLEET", "OTHER"],
                index=0, key="add_weather"
            )
            lighting_condition = st.selectbox(
                "Lighting Condition",
                ["UNKNOWN", "DAYLIGHT", "DARK - LIGHTED", "DARK - NOT LIGHTED", "DUSK/DAWN"],
                index=0, key="add_lighting"
            )
        with cols1[1]:
            first_crash_type = st.text_input(
                "First Crash Type (Specific)",
                help="More specific first contact point, if known.",
                key="add_first_crash_type"
            )
            trafficway_type = st.text_input(
                "Trafficway Type",
                help="Type of roadway (e.g., INTERSTATE, LOCAL STREET, ALLEY)",
                key="add_trafficway_type"
            )
            alignment = st.text_input(
                "Alignment",
                help="Roadway alignment (e.g., STRAIGHT AND LEVEL, CURVE ON GRADE)",
                key="add_alignment"
            )
            roadway_surface_cond = st.selectbox(
                "Roadway Surface Condition",
                ["UNKNOWN", "DRY", "WET", "SNOW/ICE", "SAND/MUD/DIRT/OIL"],
                index=0, key="add_surface_cond"
            )
        with cols1[2]:
            road_defect = st.selectbox(
                "Road Defect",
                ["NONE", "RUT, HOLES", "SHOULDER DEFECT", "DEBRIS ON ROADWAY", "OTHER"],
                index=0, key="add_road_defect"
            )
            intersection_related_i = st.selectbox(
                "Intersection Related?",
                ["NO", "YES"],
                index=0, key="add_intersection_related"
            )
            damage = st.text_input(
                "Damage Description",
                help="Brief description of property in damage.",
                key="add_damage"
            )
            prim_contributory_cause = st.text_input(
                "Primary Contributory Cause",
                help="Main factor contributing to the crash (e.g., UNSAFE SPEED, FAILED TO YIELD)",
                key="add_prim_cause"
            )
            most_severe_injury = st.selectbox(
                "Most Severe Injury",
                ["NONE", "FATAL", "INCAPACITATING", "NON-INCAPACITATING", "REPORTED, NOT EVIDENT"],
                index=0, key="add_most_severe_injury"
            )

        st.subheader("Detailed Injuries & Temporal Data")
        inj_cols = st.columns(3)
        with inj_cols[0]:
            injuries_fatal = st.number_input("Fatal Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_fatal")
            injuries_incapacitating = st.number_input("Incapacitating Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_incapacitating")
        with inj_cols[1]:
            injuries_non_incapacitating = st.number_input("Non-Incapacitating Injuries", min_value=0.0, value=0.0, step=0.1, key="add_injuries_non_incapacitating")
            injuries_reported_not_evident = st.number_input("Injuries Reported Not Evident", min_value=0.0, value=0.0, step=0.1, key="add_injuries_reported_not_evident")
        with inj_cols[2]:
            injuries_no_indication = st.number_input("Injuries No Indication", min_value=0.0, value=0.0, step=0.1, key="add_injuries_no_indication")
        
        temp_cols = st.columns(3)
        with temp_cols[0]:
            crash_hour = st.slider("Crash Hour (0-23)", 0, 23, 12, key="add_crash_hour")
        with temp_cols[1]:
            crash_day_of_week = st.slider("Day of Week (1=Monday, 7=Sunday)", 1, 7, 1, key="add_crash_day_of_week")
        with temp_cols[2]:
            crash_month = st.slider("Month (1-12)", 1, 12, datetime.now().month, key="add_crash_month")