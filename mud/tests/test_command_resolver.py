"""
COMMAND RESOLVER
"""
from mud.command_resolver import CommandResolver


class TestCommandResolver(object):
    def test_resolving_similar_commands(self):
        resolver = CommandResolver()
        resolver.add("look", "look_string")
        resolver.add("laugh", "laugh_string")

        assert "look_string" in resolver["l"]
        assert "laugh_string" in resolver["l"]
        assert "look_string" in resolver["L"]
        assert "laugh_string" in resolver["L"]

        assert "look_string" in resolver["lo"]
        assert "laugh_string" not in resolver["lo"]

        assert "look_string" in resolver["loo"]
        assert "laugh_string" not in resolver["loo"]

        assert "look_string" in resolver["look"]
        assert "laugh_string" not in resolver["look"]
        assert "look_string" in resolver["LOOK"]
        assert "laugh_string" not in resolver["LOOK"]

        resolver.remove("look", "look_string")
        resolver.remove("laugh", "laugh_string")

        assert "look_string" not in resolver["l"]
        assert "laugh_string" not in resolver["l"]

        assert "look_string" not in resolver["lo"]
        assert "laugh_string" not in resolver["lo"]

        assert "look_string" not in resolver["loo"]
        assert "laugh_string" not in resolver["loo"]

        assert "look_string" not in resolver["look"]
        assert "laugh_string" not in resolver["look"]
