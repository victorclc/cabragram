from database.postgres.connector import PsqlConnector
from database.abstract.persistable import PersistableObject
from common.helper import load_logger


class DataManager(object):
    logger = load_logger('DataManager')
    config = None
    host = None
    db = None
    user = None
    pw = None
    prefix = None
    connector = None

    @classmethod
    def init_connector(cls, connector_name):
        if connector_name == 'postgres':
            cls.connector = PsqlConnector(cls.host, cls.db, cls.user, cls.pw, cls.prefix)

    @classmethod
    def persist(cls, obj):
        if not isinstance(obj, PersistableObject):
            raise (Exception, "Not a persistable object")

        conn = None
        ret = None
        try:
            conn = cls.connector.connect()
            ret = cls.connector.persist(conn, obj)
        except Exception as ex:
            cls.logger.error(ex)
        finally:
            if conn:
                conn.close()
        return ret

    @classmethod
    def execute_query(cls, query):
        conn = None
        ret = None
        try:
            conn = cls.connector.connect()
            ret = cls.connector.execute_query(conn, query)
        except Exception as ex:
            cls.logger.error(ex)
        finally:
            if conn:
                conn.close()
        return ret

    @classmethod
    def next_sequence(cls, sequence):
        conn = None
        ret = None
        try:
            conn = cls.connector.connect()
            ret = cls.connector.next_sequence(conn, sequence)
        except Exception as ex:
            cls.logger.error(ex)
        finally:
            if conn:
                conn.close()
        return ret
