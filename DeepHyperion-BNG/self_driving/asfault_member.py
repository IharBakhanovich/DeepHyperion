from typing import Tuple, Dict

from self_driving.asfault_mutations import MetaMutator
from self_driving.asfault_tests import RoadTest
from self_driving.beamng_config import BeamNGConfig
from self_driving.beamng_evaluator import BeamNGEvaluator
from self_driving.beamng_member import BeamNGMember
from shapely.geometry import box, MultiLineString
from shapely import ops
from asfault_network import *
from road_generator import *

# code from the AsFault
MIN_NODE_DISTANCE = 0.1
B_BOX = (-250, 0, 250, 500)


def polyline_to_decalroad(polyline, widths, z=0.01):
    nodes = []
    coords = polyline.coords
    if len(coords) != len(widths):
        raise ValueError(
            'Must give as many widths as the given polyline has coords.')

    for idx, coord in enumerate(coords):
        next_coord = {'x': coord[0], 'y': coord[1],
                      'z': z, 'width': widths[idx]}
        if nodes:
            last_coord = nodes[-1]
            last_pt = Point(last_coord['x'], last_coord['y'])
            next_pt = Point(next_coord['x'], next_coord['y'])
            distance = last_pt.distance(next_pt)
            if distance > MIN_NODE_DISTANCE:
                nodes.append(next_coord)
        else:
            nodes.append(next_coord)
    return nodes


def nodes_to_coords(nodes):
    coords = list()
    for node in nodes:
        coords.append((node['x'], node['y'], node['z'], node['width']))
    return coords


# class NoMutantWasCreated(Exception):
#     """Exception raised when there was no mutant created for asfault_member in AsFaultBeamNGMember.
#
#     Attributes:
#         message -- the error message
#     """
#
#     def __init__(self, message="There was no mutant created for this AsFaultBeamNGMember"):
#         self.message = message
#         super().__init__(self.message)


class AsFaultBeamNGMember(BeamNGMember):
    '''
    The class represents the BeamNGMember, which is created from the AsFault individual.
    '''

    def _get_control_nodes(self):
        # the code of this method is from AsFault (@author Tahereh Zohdi)
        # Gets control nodes from an asfault_member, that is the instance
        # of the RoadTest class and one of the AsFaultBeamNGMember parameter.

        # Get all the spines (linestrings) for each segment of the road
        spines = [n.get_spine() for n in self.asfault_member.get_path()]
        # Combine them into a multi-linestring
        multi_line = MultiLineString(spines)
        # Merge the lines and avoid overlaps and duplicates
        street = ops.linemerge(multi_line)

        # project to start and goal
        start_proj = street.project(self.asfault_member.start, normalized=True)
        start_proj = street.interpolate(start_proj, normalized=True)
        _, street = split(street, start_proj)

        goal_proj = street.project(self.asfault_member.goal, normalized=True)
        goal_proj = street.interpolate(goal_proj, normalized=True)
        street, _ = split(street, goal_proj)

        # This controls the width of the entire road, so 8.0 means 4m lanes
        widths = [8.0, ] * len(street.coords)
        nodes = nodes_to_coords(polyline_to_decalroad(street, widths, -28.0))
        return nodes

    def _get_sample_nodes(self):
        # Define the CATMULL-ROM SPLINE
        sample_nodes = catmull_rom(self.control_nodes, self.num_spline_nodes)
        return sample_nodes

    def _get_num_spline_nodes(self):
        return RoadGenerator.NUM_SPLINE_NODES

    def _get_road_bbox(self):
        bbox_size = B_BOX
        return RoadBoundingBox(bbox_size)

    def __init__(self, asfault_member):
        self.asfault_member = asfault_member
        self.control_nodes = self._get_control_nodes()
        self.num_spline_nodes = self._get_num_spline_nodes()
        self.sample_nodes = self._get_sample_nodes()
        self.road_bbox = self._get_road_bbox()

        super().__init__(self.control_nodes, self.sample_nodes, self.num_spline_nodes, self.road_bbox)

    def clone(self):
        res = AsFaultBeamNGMember(self.asfault_member)
        # Ensure we keep the original values
        res.control_nodes = self.control_nodes
        res.sample_nodes = self.sample_nodes
        res.num_spline_nodes = self.num_spline_nodes
        res.road_bbox = self.road_bbox
        res.config = self.config
        res.problem = self.problem
        res.distance_to_boundary = self.distance_to_boundary

        return res

    def to_dict(self) -> dict:
        # List of segments (Left, right)
        return {
            'asfault_member': RoadTest.to_dict(self.asfault_member),
            # 'control_nodes': self.control_nodes,
            # 'sample_nodes': self.sample_nodes,
            # 'num_spline_nodes': self.num_spline_nodes,
            # 'road_bbox_size': self.road_bbox.bbox.bounds,
            # 'distance_to_boundary': self.distance_to_boundary
        }

    @classmethod
    def from_dict(cls, dict: Dict):
        # road_bbox = RoadBoundingBox(dict['road_bbox_size'])
        # res = BeamNGMember([tuple(t) for t in dict['control_nodes']],
        #                    [tuple(t) for t in dict['sample_nodes']],
        #                    dict['num_spline_nodes'], road_bbox)
        # res.distance_to_boundary = dict['distance_to_boundary']
        # LOAD the input required by AsFaultBeamNGMember
        asfautl_member_dict = dict['asfault_member']
        asfault_member = RoadTest.from_dict(asfautl_member_dict)
        res = AsFaultBeamNGMember(asfault_member)

        return res

    # def evaluate(self):
    #     # TODO This may be trickier
    #     if self.needs_evaluation():
    #         self.simulation = self.problem._get_evaluator().evaluate([self])
    #         print('eval mbr', self)
    #
    #     # assert not self.needs_evaluation()

    # def needs_evaluation(self):
    #     return self.distance_to_boundary is None or self.simulation is None

    # def clear_evaluation(self):
    #     self.distance_to_boundary = None

    # def is_valid(self):
    #     # Retrieve the control nodes using Tara's code from Asfault representations
    #     # TODO What's the difference?
    #     # Equidistance points that are the actual road
    #     # Ask why we check sample nodes?
    #     return (RoadPolygon.from_nodes(self.sample_nodes).is_valid() and
    #         self.road_bbox.contains(RoadPolygon.from_nodes(self.control_node[1:-1])))

    # # IS THIS REALLY NEEDED?
    # def distance(self, other: 'BeamNGMember'):
    #     # TODO
    #     # return frechet_dist(self.sample_nodes, other.sample_nodes)
    #
    #     # THIS IS DIRECTLY ACCESSING THE ATTRIBUTE
    #     return iterative_levenshtein(self.sample_nodes, other.sample_nodes)
    #     # return frechet_dist(self.sample_nodes[0::3], other.sample_nodes[0::3])

    # def to_tuple(self):
    #     import numpy as np
    #     barycenter = np.mean(self.control_nodes, axis=0)[:2]
    #     return barycenter

    def mutate(self) -> 'AsFaultBeamNGMember':
        # creating the instance of the AsFault mutator
        asfault_mutator = MetaMutator()

        # Getting a mutant of the self.asfault_member during max 10 attempts.
        # If there was no any mutant created the NoMutantWasCreated exception is raised.
        mutant = None
        for i in range(10):
            mutant = asfault_mutator.mutate(self.asfault_member)
            if mutant != None:
                break
        if mutant is None:
            raise ValueError("No gene can be mutated")

        # this piece of code creates a mutant of the self.asfault_member till it is created
        # is_there_mutant = False
        # while not is_there_mutant:
        #     mutant = asfault_mutator.mutate(self.asfault_member)
        #     if mutant != None:
        #         is_there_mutant = True

        self.asfault_member = mutant

        # Update the control and sample points using self, because those parameters don't match to tne new asfult_member
        self.control_nodes = self._get_control_nodes()
        self.num_spline_nodes = self._get_num_spline_nodes()
        self.sample_nodes = self._get_sample_nodes()
        self.road_bbox = self._get_road_bbox()

        # adjustment the distance_to_boundary value, because it is a new individual and it should be evaluated
        self.distance_to_boundary = None

        return self

    # def __repr__(self):
    #     eval_boundary = 'na'
    #     if self.distance_to_boundary:
    #         eval_boundary = str(self.distance_to_boundary)
    #         if self.distance_to_boundary > 0:
    #             eval_boundary = '+' + eval_boundary
    #         eval_boundary = '~' + eval_boundary
    #     eval_boundary = eval_boundary[:7].ljust(7)
    #     h = hashlib.sha256(str([tuple(node) for node in self.control_nodes]).encode('UTF-8')).hexdigest()[-5:]
    #     return f'{self.name_ljust} h={h} b={eval_boundary}'
