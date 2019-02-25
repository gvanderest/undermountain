from datetime import datetime
from mud import logging, settings, event
from typing import Text

import asyncio
import importlib
import traceback


class Game(object):
    def __init__(self) -> None:
        self.event_handlers = {}

        self.modules = []
        self.connections = []
        self.injectors = {}
        self.entities = {}
        self.data = {}

        self.language_strings = {
            "EN_US": {
                "SHUTDOWN_STRING": "Shutting down..",
                "EVENT_EMITTED_DEBUG_MESSAGE": "Event emitted: {{type}} {{data}}",
            },
        }
        self.language = "EN_US"

        self.setup()

        self.t = self.translate

    def setup(self) -> None:
        self.setup_modules()

    def setup_modules(self) -> None:
        module_names = settings.get("MODULES", ())

        for raw_module_name in module_names:
            # Separate package and module name.
            package_name_parts = raw_module_name.split(".")
            package_name = ".".join(package_name_parts[:-1])
            module_name = package_name_parts[-1]

            package = importlib.import_module(package_name)
            module = getattr(package, module_name)

            # Instantiate the module and store it.
            self.register_module(module)

    def register_entity(self, name: str, entity_class):
        self.entities[name] = entity_class

    def register_injector(self, name: str, injector) -> None:
        self.injectors[name] = injector(self)

    def register_module(self, module) -> None:
        instance = module(self)
        self.modules.append(instance)
        instance.setup()

    async def start_modules(self) -> None:
        for module in self.modules:
            logging.info(f"Starting module {module}.")
            await module.start()

    def handle_exception(self, e):
        output = traceback.format_exc().strip()
        self.emit("global:exception", {
            "traceback": output,
        })

    def stop_modules(self) -> None:
        for module in self.modules:
            logging.info(f"Stopping module {module}.")
            module.stop()

    def register_event_handler(self, pattern: str, handler) -> None:
        logging.debug(f"Registering event handler {pattern} to {handler}.")
        handlers = self.event_handlers.get(pattern, [])
        handlers.append(handler)
        self.event_handlers[pattern] = handlers

    def unregister_event_handler(self, pattern: str, handler) -> None:
        handlers = self.event_handlers.get(pattern, [])

        if handler in handlers:
            handlers.remove(handler)

        self.event_handlers[pattern] = handlers

        if not handlers:
            del self.event_handlers[pattern]

    async def start(self) -> None:
        self.running = True

        await self.start_modules()

        while self.running:
            await asyncio.sleep(1.0)

            now = datetime.now()
            timestamp = now.timestamp()

            self.emit("global:tick", {"timestamp": now.timestamp()})

    def translate(self, reference: str, **values) -> str:
        """Translate a string."""
        parts = reference.split(".")

        node = self.language_strings.get(self.language, {})

        while parts:
            part = parts.pop(0)

            if part not in node:
                return reference

            node = node.get(part, {})

        interpolated = node

        for (key, value) in values.items():
            interpolated = interpolated.replace(f"{{{{{key}}}}}", str(value))

        return interpolated

    def emit_event(self, event: event.Event) -> event.Event:
        """Emit an event object."""

        type = event.type
        data = event.data

        logging.debug(self.t("EVENT_EMITTED_DEBUG_MESSAGE", type=type, data=data))

        parts = type.split(":")

        for index in range(len(parts)):
            final_pattern = index == len(parts) - 1

            if final_pattern:
                pattern = ":".join(parts)
            else:
                pattern = ":".join(parts[:index+1] + ["*"])

            for handler in self.event_handlers.get(pattern, []):
                handler(event)

                if event.blocked:
                    return event

        return event

    def emit(self, type: str, data: object=None, blockable: bool=True) -> event.Event:
        """Generate an Event object and emit it to the world."""
        ev = event.Event(type, data, blockable=blockable)
        return self.emit_event(ev)

    def stop(self) -> None:
        self.stop_modules()

        self.running = False
