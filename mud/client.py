class Client(object):
    STATE_LOGIN_NAME = "login_name"
    STATE_LOGIN_PASSWORD = "login_password"
    STATE_LOGIN_RECONNECT = "login_reconnect"
    STATE_CONFIRM_NAME = "confirm_name"
    STATE_SELECT_PASSWORD = "select_password"
    STATE_CONFIRM_PASSWORD = "confirm_password"
    STATE_SELECT_RACE = "select_race"
    STATE_SELECT_GENDER = "select_gender"
    STATE_SELECT_CLASS = "select_class"
    STATE_CUSTOMIZING = "customizing"
    STATE_CONFIRM_CUSTOMIZE = "confirm_customize"
    STATE_SELECT_ALIGNMENT = "select_alignment"
    STATE_SELECT_WEAPON = "select_weapon"
    STATE_MOTD = "motd"
    STATE_PLAYING = "playing"

    def __init__(self, connection):
        self.connection = connection
        self.actor = None
        self.commands = []
        self.state = self.STATE_LOGIN_NAME

    def init(self):
        pass

    def write(self, message):
        self.connection.write(message)

    def writeln(self, message):
        self.connection.writeln(message)

    def get_game(self):
        return self.connection.get_game()

    def handle_input(self, input):
        method_name = "handle_{}_input".format(self.state)
        method = getattr(self, method_name)
        line = input.rstrip()
        return method(line)

    def handle_output(self, output):
        self.write(output)

    def set_actor(self, actor):
        self.actor = actor

    def get_actor(self):
        return self.actor

    def quit(self):
        self.connection.close()
