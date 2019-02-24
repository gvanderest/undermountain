from mud import module, manager


class Core(module.Module):
    def setup(self):
        self.add_module(self.Battle)

    class Battle(module.Module):
        pass
