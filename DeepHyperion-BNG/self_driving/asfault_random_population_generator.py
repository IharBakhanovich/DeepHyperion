import os
import json

from self_driving.asfault_member import AsFaultBeamNGMember
from self_driving.asfault_tests import RoadTestFactory, RoadTest
from self_driving.asfault_evolution_config import EvolutionConfig as c

from shapely.geometry import box, MultiLineString
from shapely import ops
from asfault_network import *
from road_generator import *

# code from the AsFault for the testing fetching of sample_nodes
MIN_NODE_DISTANCE = 0.1
B_BOX = (-250, 0, 250, 500)


# for the testing
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


# for the testing
def nodes_to_coords(nodes):
    coords = list()
    for node in nodes:
        coords.append((node['x'], node['y'], node['z'], node['width']))
    return coords


def generate_random_test(size):
    # creating a directory to save individuals
    if not os.path.exists(c.DIR_TO_SAVE):
        os.makedirs(c.DIR_TO_SAVE)

    # creating a roadTestFactory
    roadTestFactory = RoadTestFactory(size)
    # rg = RoadGenerator(bounds).generate_factories()
    # rg.generate_factories()
    return roadTestFactory.generate_random_test()
    # # Generate the dictionary
    # asfault_member_as_dictionary = asfault_member.to_dict(asfault_member)
    # id = asfault_member_as_dictionary['test_id']
    # with open(os.path.join(c.DIR_TO_SAVE, str(id) + '_random_test.json'), 'w') as fp:
    #     json.dump(asfault_member_as_dictionary, fp)
    #


def save_road_test_to_json_file(road_test):
    asfault_member_as_dictionary = RoadTest.to_dict(road_test)
    id = asfault_member_as_dictionary['test_id']
    with open(os.path.join(c.DIR_TO_SAVE, str(id) + '_random_test.json'), 'w') as fp:
        json.dump(asfault_member_as_dictionary, fp)


def fetch_road_test_instance_from_json_file(file):
    '''
    Fetches the RoadTest instance of AsFault from json file.

    Parameters:
        file -- is the path to the .json file
    '''
    with open(file, 'r') as infile:
        test_dict = json.loads(infile.read())
    return RoadTest.from_dict(test_dict)
    # return json.loads(file, object_hook=RoadTest.from_dict)


# for the testing
def get_control_nodes(asfault_member):
    # Get all the spines (linestrings) for each segment of the road
    spines = [n.get_spine() for n in asfault_member.get_path()]
    # Combine them into a multi-linestring
    multi_line = MultiLineString(spines)
    # Merge the lines and avoid overlaps and duplicates
    street = ops.linemerge(multi_line)

    # project to start and goal
    start_proj = street.project(asfault_member.start, normalized=True)
    start_proj = street.interpolate(start_proj, normalized=True)
    _, street = split(street, start_proj)

    goal_proj = street.project(asfault_member.goal, normalized=True)
    goal_proj = street.interpolate(goal_proj, normalized=True)
    street, _ = split(street, goal_proj)

    # This controls the width of the entire road, so 8.0 means 4m lanes
    widths = [8.0, ] * len(street.coords)
    nodes = nodes_to_coords(polyline_to_decalroad(street, widths, -28.0))
    return nodes


# for the testing
def get_sample_nodes(control_nodes, num_spline_nodes):
    sample_nodes = catmull_rom(control_nodes, num_spline_nodes)
    return sample_nodes


# for the testing
def get_num_spline_nodes():
    return RoadGenerator.NUM_SPLINE_NODES


# for the testing
def get_road_bbox():
    bbox_size = B_BOX
    return RoadBoundingBox(bbox_size)


# for tests invoking
def main():
    # # to test the creation of RoadTest instance and to save it to .json
    # # size = 500
    # # bounds = box(-size, -size, size, size)
    # # dir_to_save = '../generated_individuals'
    # size = c.BOUNDS
    # quantity = 5
    # for i in range(1, quantity):
    #     save_road_test_to_json_file(generate_random_test(size))
    #
    # file = c.DIR_TO_SAVE + '/' + '1_random_test.json'
    # road_test = fetch_road_test_instance_from_json_file(file)
    # # road_test['test_id'] = 100
    # save_road_test_to_json_file(road_test)
    #
    #

    # if not os.path.exists(c.DIR_TO_SAVE):
    #     os.makedirs(c.DIR_TO_SAVE)
    # creating a roadTestFactory
    roadTestFactory = RoadTestFactory(c.BOUNDS)
    # # # rg = RoadGenerator(bounds).generate_factories()
    # # # rg.generate_factories()
    # for i in range(0, 12):
    #     asfault_member = roadTestFactory.generate_random_test()
    #     # Generate the dictionary
    #     asfault_member_as_dictionary = asfault_member.to_dict(asfault_member)
    #     id = asfault_member_as_dictionary['test_id']
    #     with open(os.path.join(c.DIR_TO_SAVE, 'seed'+ str(id) + '.json'), 'w') as fp:
    #         json.dump(asfault_member_as_dictionary, fp)

    # to test fetching sample_nodes from RoadTest instance and creating the AsFaultBeamNGMember
    # creating the RoadTest instance
    size = c.BOUNDS
    asfault_member = generate_random_test(size)
    control_nodes = get_control_nodes(asfault_member)
    # print(control_nodes)
    num_spline_nodes = get_num_spline_nodes()
    sample_nodes = get_sample_nodes(control_nodes, num_spline_nodes)
    road_bbox = get_road_bbox()
    res = BeamNGMember(control_nodes, sample_nodes, num_spline_nodes, road_bbox)
    beamNGMember_to_dict = res.to_dict()
    beamNGMember_from_dict = BeamNGMember.from_dict(beamNGMember_to_dict)
    # res_asf = AsFaultBeamNGMember(asfault_member)
    # to test mutation
    # mutant_res_asf = res_asf.mutate()
    # res_asf_to_dict = res_asf.to_dict()
    # asfault_member_from_dict = AsFaultBeamNGMember.from_dict(res_asf_to_dict)
    # print(res_asf_to_dict)
    print(road_bbox)


if __name__ == "__main__":
    main()
