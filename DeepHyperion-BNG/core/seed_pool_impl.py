from typing import Dict

from core.problem import Problem
from core.member import Member
from core.folder_storage import SeedStorage
from core.folders import folders
from core.seed_pool import SeedPool
from self_driving.asfault_member import AsFaultBeamNGMember
from self_driving.asfault_random_population_generator import fetch_road_test_instance_from_json_file


class SeedPoolFolder(SeedPool):
    def __init__(self, problem: Problem, folder_name):
        super().__init__(problem)
        self.storage = SeedStorage(folder_name)
        self.file_path_list = self.storage.all_files()
        assert (len(self.file_path_list)) > 0
        self.cache: Dict[str, Member] = {}

    def __len__(self):
        return len(self.file_path_list)

    def __getitem__(self, item) -> Member:
        path = self.file_path_list[item]
        if self.problem.config.generator_name == self.problem.config.GEN_DIVERSITY:
            return path
        else:
            result: Member = self.cache.get(path, None)
            if not result:
                if self.problem.member_class() is AsFaultBeamNGMember:
                    asfault_member = fetch_road_test_instance_from_json_file(path)
                    result = AsFaultBeamNGMember(asfault_member)
                else:
                    result = self.problem.member_class().from_dict(self.storage.read(path))
                self.cache[path] = result
            result.problem = self.problem
            return result


class SeedPoolRandom(SeedPool):
    def __init__(self, problem, n):
        super().__init__(problem)
        self.n = n
        self.seeds = [problem.generate_random_member() for _ in range(self.n)]

    def __len__(self):
        return self.n

    def __getitem__(self, item):
        return self.seeds[item]


class SeedPoolMnist(SeedPool):
    def __init__(self, problem: Problem, filename):
        super().__init__(problem)
        content = folders.member_seeds.joinpath(filename).read_text()
        self.seeds_index = content.split(',')
        self.cache: Dict[str, Member] = {}

    def __len__(self):
        return len(self.seeds_index)

    def __getitem__(self, item) -> Member:
        mnist_index = self.seeds_index[item]
        result: Member = self.cache.get(mnist_index, None)
        if not result:
            # result = self.problem.member_class().from_dict(self.storage.read(path))
            raise NotImplemented()
            self.cache[mnist_index] = result
        return result