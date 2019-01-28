import configparser


class Configuration:
    def __init__(self, ini_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(ini_file)

    def get_db_engine_string(self):
        """
        Generates the mysql connection string, ready for SQLAlchemy
        :return:
        """
        return self.config.get('Database', 'dialect', fallback='mysql+pymysql') + \
            '://' + self.config.get('Database', 'user', fallback='root') + \
            ':' + self.config.get('Database', 'password', fallback='password') + \
            '@' + self.config.get('Database', 'host', fallback='localhost') + \
            '/' + self.config.get('Database', 'database', fallback='scrapebot')

    def add_section(self, section):
        if section not in self.config:
            self.config[section] = {}

    def add_value(self, section, name, value):
        self.add_section(section)
        self.config[section][name] = str(value)

    def write(self):
        try:
            with open('config.ini', 'w') as configfile:
                self.config.write(configfile)
                return True
        except:
            return False
