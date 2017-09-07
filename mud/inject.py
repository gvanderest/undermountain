def inject(*names):
    def decorator(func):
        def decorate(self, *args, **kwargs, ):
            game = self.get_game()

            # injectors = {}

            for name in names:
                kwargs[name] = game.get_injector(name)

            args = (self,) + args

            return func(*args, **kwargs)
        return decorate
    return decorator
