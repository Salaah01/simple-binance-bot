from configparser import ConfigParser
import psycopg2


def connection(filename: str = 'database.ini', section: str = 'postgresql'):
    """Fetches the database connection parameters by parsing the connection
    .ini file.

    Args:
        filename - (str) .ini filename.
        section - (str) Section relating to the database config in the .ini.

    Returns:
        Database connection.
    """
    parser = ConfigParser()
    parser.read(filename)

    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]

    else:
        raise Exception(f'Section {section} not found in {filename}.')

    return psycopg2.connect(
        f"dbname={db['database']} user={db['user']} password={db['password']} host={db.get('host', 'localhost')} port={db.get('port', 5432)}"  # noqa: E501
    )
