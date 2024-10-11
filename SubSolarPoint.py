import math
from datetime import datetime, timedelta

class Constants:
    coordinates_string_format = "{:3d}° {:02d}' {}  {:3d}° {:02d}' {}"
    degrees_longitude_per_hour = 15
    degrees_to_radians = 0.01745329252
    earth_tilt_in_degrees = 23.43715
    earth_tilt_in_radians = 0.40905543478
    julian_date_for_jan_01_1970_at_0000_gmt = 2440587.5
    noon_time = 12
    number_of_days_in_a_century = 36525
    number_of_days_in_a_year = 365
    number_of_hours_in_a_day = 24
    number_of_minutes_in_a_day = 1440
    number_of_minutes_in_a_year = number_of_days_in_a_year * number_of_minutes_in_a_day
    number_of_minutes_in_an_hour = 60
    number_of_seconds_in_a_day = 86400
    number_of_seconds_in_a_minute = 60
    number_of_seconds_in_a_year = number_of_seconds_in_a_day * number_of_days_in_a_year
    number_of_seconds_in_an_hour = 3600
    one_eighty_degrees = 180
    radians_to_degrees = 57.2957795131
    three_sixty_degrees = 360

class CoordinateConversions:
    @staticmethod
    def decimal_coordinates_to_deg_min_sec(latitude, longitude, format_string):
        lat_seconds = int(latitude * Constants.number_of_seconds_in_an_hour)
        lat_degrees = lat_seconds // Constants.number_of_seconds_in_an_hour
        lat_seconds = abs(lat_seconds % Constants.number_of_seconds_in_an_hour)
        lat_minutes = lat_seconds // Constants.number_of_seconds_in_a_minute
        lat_seconds %= Constants.number_of_seconds_in_a_minute

        lon_seconds = int(longitude * Constants.number_of_seconds_in_an_hour)
        lon_degrees = lon_seconds // Constants.number_of_seconds_in_an_hour
        lon_seconds = abs(lon_seconds % Constants.number_of_seconds_in_an_hour)
        lon_minutes = lon_seconds // Constants.number_of_seconds_in_a_minute
        lon_seconds %= Constants.number_of_seconds_in_a_minute

        return format_string.format(
            abs(lat_degrees), lat_minutes, "North" if lat_degrees >= 0 else "South",
            abs(lon_degrees), lon_minutes, "East" if lon_degrees >= 0 else "West"
        )

class Astrocalculations:
    @staticmethod
    def jd_from_date(date):
        j_d = Constants.julian_date_for_jan_01_1970_at_0000_gmt + date.timestamp() / Constants.number_of_seconds_in_a_day
        return j_d

    @staticmethod
    def julian_century_since_jan_2000(date):
        return (Astrocalculations.jd_from_date(date) - 2451545) / Constants.number_of_days_in_a_century

    @staticmethod
    def orbit_eccentricity_of_earth(t):
        return 0.016708634 - t * (0.000042037 + 0.0000001267 * t)

    @staticmethod
    def mean_anomaly(t):
        return 357.52911 + t * 35999.05029 - t * 0.0001537

    @staticmethod
    def geometric_mean_longitude_of_sun_at_current_time(t):
        return (280.46646 + t * 36000.76983 + t * t * 0.0003032) % Constants.three_sixty_degrees

    @staticmethod
    def sun_equation_of_center(t):
        m = Astrocalculations.mean_anomaly(t)
        return (math.sin(m * Constants.degrees_to_radians) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
                math.sin(2 * m * Constants.degrees_to_radians) * (0.019993 - 0.000101 * t) +
                math.sin(3 * m * Constants.degrees_to_radians) * 0.000289)

    @staticmethod
    def latitude_of_sun(date):
        jC = Astrocalculations.julian_century_since_jan_2000(date)
        geom_mean_longitude = Astrocalculations.geometric_mean_longitude_of_sun_at_current_time(jC)
        sun_true_longitude = geom_mean_longitude + Astrocalculations.sun_equation_of_center(jC)
        latitude_of_sun = math.asin(math.sin(sun_true_longitude * Constants.degrees_to_radians) * math.sin(Constants.earth_tilt_in_radians))
        return latitude_of_sun * Constants.radians_to_degrees

    @staticmethod
    def equation_of_time(date):
        t = Astrocalculations.julian_century_since_jan_2000(date)
        mean_longitude_sun_radians = Astrocalculations.geometric_mean_longitude_of_sun_at_current_time(t) * Constants.degrees_to_radians
        mean_anomaly_sun_radians = Astrocalculations.mean_anomaly(t) * Constants.degrees_to_radians
        eccentricity = Astrocalculations.orbit_eccentricity_of_earth(t)
        obliquity = 0.0430264916545165

        term1 = obliquity * math.sin(2 * mean_longitude_sun_radians)
        term2 = 2 * eccentricity * math.sin(mean_anomaly_sun_radians)
        term3 = 4 * eccentricity * obliquity * math.sin(mean_anomaly_sun_radians) * math.cos(2 * mean_longitude_sun_radians)
        term4 = 0.5 * obliquity * obliquity * math.sin(4 * mean_longitude_sun_radians)
        term5 = 1.25 * eccentricity * eccentricity * math.sin(2 * mean_anomaly_sun_radians)

        return 4 * (term1 - term2 + term3 - term4 - term5) * Constants.radians_to_degrees

    @staticmethod
    def sub_solar_longitude_of_sun_at_current_time(date):
        eOT = Astrocalculations.equation_of_time(date)
        local_time = datetime.utcnow().hour + datetime.utcnow().minute / 60
        gmt = (local_time - eOT / Constants.number_of_minutes_in_an_hour) % Constants.number_of_hours_in_a_day
        noon_hour_delta = (Constants.noon_time - gmt) % Constants.number_of_hours_in_a_day
        sub_solar_lon = noon_hour_delta * Constants.degrees_longitude_per_hour
        return sub_solar_lon

    @staticmethod
    def get_sub_solar_coordinates():
        now = datetime.utcnow()
        lat = Astrocalculations.latitude_of_sun(now)
        lon = Astrocalculations.sub_solar_longitude_of_sun_at_current_time(now)
        return lat, lon

if __name__ == "__main__":
    import time
    secs_to_delay = 5

    while True:
        now = datetime.now()
        formatted_time = now.strftime("%m-%d-%y %H:%M:%S")
        print("Formatted local time:", formatted_time)
        subsolar_point = Astrocalculations.get_sub_solar_coordinates()
        lat, lon = subsolar_point
        coordinates = CoordinateConversions.decimal_coordinates_to_deg_min_sec(lat, lon, Constants.coordinates_string_format)
        print(f"The subsolar point is now at: {coordinates} (at {now})")
        time.sleep(secs_to_delay)
