def inject(*injector_names):

    def decorator(func):

        def wrapper(self, *args, **kwargs):
            for name in injector_names:
                kwargs[name] = self.game.get_injector(name)
            return func(self, *args, **kwargs)

        return wrapper

    return decorator
