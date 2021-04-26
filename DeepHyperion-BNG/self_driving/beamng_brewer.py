from beamngpy import BeamNGpy, Scenario, Vehicle
from beamngpy.sensors import Camera
from core.folder_storage import SeedStorage
from self_driving.beamng_config import BeamNGConfig
from self_driving.beamng_member import BeamNGMember

from self_driving.decal_road import DecalRoad
from self_driving.road_points import List4DTuple, RoadPoints
from self_driving.simulation_data import SimulationParams
from self_driving.beamng_pose import BeamNGPose


class BeamNGCamera:
    def __init__(self, beamng: BeamNGpy, name: str, camera: Camera = None):
        self.name = name
        self.pose: BeamNGPose = BeamNGPose()
        self.camera = camera
        if not self.camera:
            self.camera = Camera((0, 0, 0), (0, 0, 0), 120, (1280, 1280), colour=True, depth=True, annotation=True)
        self.beamng = beamng

    def get_rgb_image(self):
        self.camera.pos = self.pose.pos
        self.camera.direction = self.pose.rot
        cam = self.beamng.render_cameras()
        img = cam[self.name]['colour'].convert('RGB')
        return img


class BeamNGBrewer:
    def __init__(self, road_nodes: List4DTuple = None, beamng_home=None):
        self.beamng = BeamNGpy('localhost', 64256, home=beamng_home)
        self.vehicle: Vehicle = None
        self.camera: BeamNGCamera = None
        if road_nodes:
            self.setup_road_nodes(road_nodes)
        steps = 5
        self.params = SimulationParams(beamng_steps=steps, delay_msec=int(steps * 0.05 * 1000))
        self.vehicle_start_pose = BeamNGPose()

    def setup_road_nodes(self, road_nodes):
        self.road_nodes = road_nodes
        self.decal_road: DecalRoad = DecalRoad('street_1').add_4d_points(road_nodes)
        self.road_points = RoadPoints().add_middle_nodes(road_nodes)

    def setup_vehicle(self) -> Vehicle:
        assert self.vehicle is None
        self.vehicle = Vehicle('ego_vehicle', model='etk800', licence='TIG', color='Red')
        return self.vehicle

    def setup_scenario_camera(self, resolution=(1280, 1280), fov=120) -> BeamNGCamera:
        assert self.camera is None
        self.camera = BeamNGCamera(self.beamng, 'brewer_camera')
        return self.camera

    def bring_up(self):
        self.scenario = Scenario('tig', 'tigscenario')
        if self.vehicle:
            self.scenario.add_vehicle(self.vehicle, pos=self.vehicle_start_pose.pos, rot=self.vehicle_start_pose.rot)

        if self.camera:
            self.scenario.add_camera(self.camera.camera, self.camera.name)

        self.scenario.make(self.beamng)
        if not self.beamng.server:
            self.beamng.open()
        self.beamng.pause()
        self.beamng.set_deterministic()
        self.beamng.load_scenario(self.scenario)
        self.beamng.start_scenario()

    def __del__(self):
        if self.beamng:
            try:
                self.beamng.close()
            except:
                pass


if __name__ == '__main__':
    config = BeamNGConfig()
    brewer = BeamNGBrewer()
    vehicle = brewer.setup_vehicle()
    camera = brewer.setup_scenario_camera()
    while True:
        seed_storage = SeedStorage('basic5')
        for i in range(1, 11):
            member = BeamNGMember.from_dict(seed_storage.load_json_by_index(i))
            brewer.setup_road_nodes(member.sample_nodes)
            brewer.vehicle_start_pose = brewer.road_points.vehicle_start_pose()
            brewer.bring_up()
            print('bring up ok')
            brewer.beamng.resume()
            print('resumed')
            input('waiting keypress...')
            print('key received')
            brewer.beamng.stop_scenario()
