import json

class EvolutionConfig:
    LANE_WIDTH = 4.0
    # Note that to claim an OBE at least half of the car is already out...
    TOLERANCE = 0.0

    L_LANES = 1
    R_LANES = 1
    MAX_ANGLE = 5.0
    BOUNDS = 500
    POP_SIZE = 25
    MUT_CHANCE = 0.05
    INTRO_CHANCE = 0.15
    EVALUATOR = 'lanedist'
    SELECTOR = 'tournament'
    ESTIMATOR = 'length'
    JOIN_PROBABILITY = 0.5
    PARTIAL_MERGE_M_COUNT = 1
    PARTIAL_MERGE_D_COUNT = 1
    TRY_ALL_OPS = True

    ATTEMPT_REPAIR = False
    SEARCH_STOPPER = None

    DIR_TO_SAVE = '../generated_individuals'

    @staticmethod
    def get_default():
        ret = {}

        ret['lane_width'] = EvolutionConfig.LANE_WIDTH
        ret['tolerance'] = EvolutionConfig.TOLERANCE

        ret['l_lanes'] = EvolutionConfig.L_LANES
        ret['r_lanes'] = EvolutionConfig.R_LANES
        ret['max_angle'] = EvolutionConfig.MAX_ANGLE
        ret['bounds'] = EvolutionConfig.BOUNDS
        ret['pop_size'] = EvolutionConfig.POP_SIZE
        ret['mut_chance'] = EvolutionConfig.MUT_CHANCE
        ret['intro_chance'] = EvolutionConfig.INTRO_CHANCE
        ret['evaluator'] = EvolutionConfig.EVALUATOR
        ret['selector'] = EvolutionConfig.SELECTOR
        ret['estimator'] = EvolutionConfig.ESTIMATOR
        ret['join_probability'] = EvolutionConfig.JOIN_PROBABILITY
        ret['partial_merge_m_count'] = EvolutionConfig.PARTIAL_MERGE_M_COUNT
        ret['partial_merge_d_count'] = EvolutionConfig.PARTIAL_MERGE_D_COUNT
        ret['try_all_ops'] = EvolutionConfig.TRY_ALL_OPS

        ret['attempt_repair'] = EvolutionConfig.ATTEMPT_REPAIR
        ret['search_stopper'] = EvolutionConfig.SEARCH_STOPPER

        return ret

    def __init__(self, path):
        with open(path, 'r') as infile:
            cfg = json.loads(infile.read())

        self.lane_width = cfg.get('lane_width', EvolutionConfig.LANE_WIDTH)
        self.tolerance = cfg.get('tolerance', EvolutionConfig.TOLERANCE)

        self.l_lanes = cfg.get('l_lanes', EvolutionConfig.L_LANES)
        self.r_lanes = cfg.get('r_lanes', EvolutionConfig.R_LANES)
        self.max_angle = cfg.get('max_angle', EvolutionConfig.MAX_ANGLE)
        self.bounds = cfg.get('bounds', EvolutionConfig.BOUNDS)
        self.pop_size = cfg.get('pop_size', EvolutionConfig.POP_SIZE)
        self.mut_chance = cfg.get('mut_chance', EvolutionConfig.MUT_CHANCE)
        self.intro_chance = cfg.get('intro_chance', EvolutionConfig.INTRO_CHANCE)
        self.evaluator = cfg.get('evaluator', EvolutionConfig.EVALUATOR)
        self.selector = cfg.get('selector', EvolutionConfig.SELECTOR)
        self.estimator = cfg.get('estimator', EvolutionConfig.ESTIMATOR)
        self.join_probability = cfg.get('join_probability', EvolutionConfig.JOIN_PROBABILITY)
        self.partial_merge_m_count = cfg.get('partial_merge_m_count', EvolutionConfig.PARTIAL_MERGE_M_COUNT)
        self.partial_merge_d_count = cfg.get('partial_merge_d_count', EvolutionConfig.PARTIAL_MERGE_D_COUNT)
        self.try_all_ops = cfg.get('try_all_ops', EvolutionConfig.TRY_ALL_OPS)

        self.attempt_repair = cfg.get('attempt_repair', EvolutionConfig.ATTEMPT_REPAIR)
        self.search_stopper = cfg.get('search_stopper', EvolutionConfig.SEARCH_STOPPER)