from datetime import datetime
from mud import logging, settings
from typing import Text

import asyncio
import importlib


class Game(object):
    def __init__(self):
        self.event_handlers = {}

        self.modules = []
        self.connections = []

        self.language_strings = {
            "EN_US": {
                "SHUTDOWN_STRING": "Shutting down..",
                "EVENT_EMITTED_DEBUG_MESSAGE": "Event emitted: {{type}} {{data}}",
            },
        }
        self.language = "EN_US"

        self.setup()

        self.t = self.translate

    def setup(self):
        self.setup_modules()

    def setup_modules(self):
        module_names = settings.get("MODULES", ())

        for raw_module_name in module_names:
            # Separate package and module name.
            package_name_parts = raw_module_name.split(".")
            package_name = ".".join(package_name_parts[:-1])
            module_name = package_name_parts[-1]

            package = importlib.import_module(package_name)
            module = getattr(package, module_name)

            # Instantiate the module and store it.
            self.add_module(module)

    def add_module(self, module):
        instance = module(self)
        # TODO: Debug
        self.modules.append(instance)
        instance.setup()

    async def start_modules(self):
        for module in self.modules:
            logging.info(f"Starting module {module}.")
            await module.start()

    def stop_modules(self):
        for module in self.modules:
            logging.info(f"Stopping module {module}.")
            module.stop()

    def add_event_handler(self, pattern, handler):
        handlers = self.event_handlers.get(pattern, [])
        handlers.append(handler)
        self.event_handlers[pattern] = handlers

    def remove_event_handler(self, pattern, handler):
        handlers = self.event_handlers.get(pattern, [])

        if handler in handlers:
            handlers.remove(handler)

        self.event_handlers[pattern] = handlers

        if not handlers:
            del self.event_handlers[pattern]

    async def start(self):
        self.running = True

        await self.start_modules()

        while self.running:
            await asyncio.sleep(1.0)

            now = datetime.now()
            timestamp = now.timestamp()

            self.emit("global:tick", {"timestamp": now.timestamp()})

    def translate(self, reference, **values):
        """Translate a string."""
        parts = reference.split(".")

        node = self.language_strings.get(self.language, {})

        while parts:
            part = parts.pop(0)

            if part not in node:
                return reference

            node = node.get(part, {})

        interpolated = node
        print(values)
        for (key, value) in values.items():
            interpolated = interpolated.replace(f"{{{{{key}}}}}", str(value))

        return interpolated

    def emit(self, type: str, data: object=None) -> None:
        """Emit an event."""
        if data is None:
            data = {}

        logging.debug(self.t("EVENT_EMITTED_DEBUG_MESSAGE", type=type, data=data))

        parts = type.split(":")

        for index in range(len(parts)):
            final_pattern = index == len(parts) - 1

            if final_pattern:
                pattern = ":".join(parts)
            else:
                pattern = ":".join(parts[:index+1] + ["*"])

            for handler in self.event_handlers.get(pattern, []):
                handler(type, data)

    def stop(self):
        self.stop_modules()

        self.running = False
