import inspect


def inject(*injector_names):
    """Extract Game injectors to provide to the function."""
    def injector_fetcher(func):
        def injector_linker(*args, **kwargs):
            # Iterate through normal arguments.
            arg_names = inspect.getfullargspec(func)[0]
            for arg in args:
                key_name = arg_names.pop(0)
                kwargs[key_name] = arg

            # Extract the "self" keyword.
            self = kwargs["self"]

            # Inject anything that was requested.
            for injector_name in injector_names:
                kwargs[injector_name] = self.game.injectors.get(injector_name)

            # Apply all arguments to function.
            return func(**kwargs)
        return injector_linker
    return injector_fetcher
