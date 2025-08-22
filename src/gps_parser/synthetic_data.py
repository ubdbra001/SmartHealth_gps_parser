import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from geopy.point import Point
from geopy.distance import geodesic

class SynthGPSGen:

    def __init__(
            self,
            journey_params: list[dict[str: int|float]],
            sampling_params: dict[str: int],
            starting_time: datetime,
            staring_coords: dict[str: float],
            starting_orientation: int):
        
        self.journey_params = journey_params
        self.sampling_params = sampling_params

        self.starting_time = starting_time
        self.starting_coords = staring_coords
        self.starting_orientation = starting_orientation

        self.gps_points = [Point(**staring_coords)]
        self.time_points = [starting_time]

        self.time_diffs = np.array([])
        self.distances = np.array([])
        self.orientations = np.array([])


    def generate_journey(self):
        for section in self.journey_params:
            n_points = section["duration"]*60//self.sampling_params["average"]

            time_diffs = self.generate_time_diffs(n_points)
            distances = self.generate_distances(time_diffs, section["speed"])
            orientations = self.generate_orientations(n_points, section["orient_change_range"])

            self.time_diffs = np.concat((self.time_diffs, time_diffs))
            self.distances = np.concat((self.distances, distances))
            self.orientations = np.concat((self.orientations, orientations))

        self.generate_times()
        self.generate_gps_points()
        

    def generate_time_diffs(self, n_points):
        return np.random.randint(
            self.sampling_params["lower"],
            self.sampling_params["upper"]+1,
            size = n_points)
    
    @staticmethod
    def generate_distances(time_diffs, speed):
        return time_diffs * speed

    def generate_times(self):
        cumulative_diffs = self.time_diffs.cumsum()
        diff_deltas = np.array([timedelta(seconds=secs) for secs in cumulative_diffs.tolist()])
        times = self.time_points[-1] + diff_deltas
        self.time_points += times.tolist()

    def generate_orientations(self, n_points, orient_change_range):
        orientation_diff_array = np.random.randint(
            -orient_change_range, 
            orient_change_range+1, 
            size = n_points)
        return orientation_diff_array.cumsum()

    def generate_gps_points(self):

        zipped_deltas = zip(self.distances, self.orientations)

        for distance, orientation in zipped_deltas:
            start_point = self.gps_points[-1]

            dist_km = distance/1000

            destination_point = geodesic(kilometers=dist_km).destination(point=start_point, bearing=orientation)

            self.gps_points.append(destination_point)

    def generate_output_dict(self):

        zipped_points = zip(self.time_points,
                            self.gps_points)
        
        self.dataset = [{"d": time.strftime("%Y-%m-%dT%H:%M:%S"),
                         "lat": points.latitude,
                         "long": points.longitude} 
                        for time, points in zipped_points]
        
        self.output = {'gps-coordinates': {'dataset': self.dataset} }

    def save_output_json(self, file_name: str, file_path: str = '.'):

        
        full_path = Path(file_path) / file_name
        full_path.parent.mkdir(exist_ok=True)

        with open(full_path, "w") as json_file:
            json.dump(self.output, json_file, indent=4)