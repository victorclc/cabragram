from database.abstract.connector import Connector
from common.helper import load_logger
import psycopg2.extras
import psycopg2
import re


class PsqlConnector(Connector):
    logger = load_logger('DataConnector')

    def connect(self):
        return psycopg2.connect(host=self.host, database=self.db, user=self.user, password=self.pw)

    def persist(self, conn, obj):
        try:
            result = None
            cursor = conn.cursor()
            query = self.discovery_query_for_object(obj)

            if query:
                cursor.execute(query)
                result = cursor.fetchone()
            if result:
                query = self.update_query_for_object(obj)
            else:
                query = self.insert_query_for_object(obj)

            cursor.execute(query)
            conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError, psycopg2.ProgrammingError) as ex:
            self.logger.error(ex)
            raise ex

    def discovery_query_for_object(self, obj):
        pers = obj.persistables()
        if '__key__' not in pers:
            return None

        if type(pers['__key__']) == list:
            for key in pers['__key__']:
                if pers[key] is None:
                    return None
        elif pers[pers['__key__']] is None:
            return None

        table = self.__table_name(obj) if '__table__' not in pers else pers['__table__']
        query = "SELECT * FROM %s WHERE %s" % (table, self.__where_clause(pers))
        self.logger.debug('Discovery query: ' + query)
        return query

    def insert_query_for_object(self, obj):
        pers = obj.persistables()
        table = self.__table_name(obj) if '__table__' not in pers else pers['__table__']
        columns = "("
        values = "("

        for key, value in pers.items():
            if key in ['__key__', '__table__'] or value is None:
                continue
            columns += key + ","
            if not isinstance(value, str) or re.search('.*\(.*\)', value):
                # numeric or procedure
                values += "%s," % value
            else:
                values += "'%s'," % value
        columns = columns[:-1] + ")"
        values = values[:-1] + ")"
        query = "INSERT INTO %s %s VALUES %s" % (table, columns, values)
        self.logger.debug("Insert query: " + query)
        return query

    def update_query_for_object(self, obj):
        pers = obj.persistables()
        pk = pers['__key__']
        table = self.__table_name(obj) if '__table__' not in pers else pers['__table__']
        query = "UPDATE %s SET " % table

        for key, value in pers.items():
            if key in ['__key__', '__table__'] or key == pk:
                continue

            if not isinstance(value, str) or re.search('.*\(.*\)', value):
                # numeric or procedure
                query += "%s=%s," % (key, str(value))
            else:
                query += "%s='%s'," % (key, str(value))

        query = query[:-1] + " WHERE " + self.__where_clause(pers)
        self.logger.debug("Update query: " + query)

        return query

    def execute_query(self, conn, query):
        result = None
        try:
            if 'select' in query.lower():
                cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                cursor.execute(query)
                result = cursor.fetchall()
            else:
                cursor = conn.cursor()
                cursor.execute(query)
                conn.commit()
            cursor.close()
        except (Exception, psycopg2.DatabaseError) as ex:
            self.logger.error(ex)
        return result

    def next_sequence(self, conn, sequence):
        res = self.execute_query(conn, "SELECT nextval('%s')" % sequence)

        if 'nextval' in res[0]:
            return res[0]['nextval']
        return None

    def __table_name(self, obj):
        table = self.prefix
        for ch in type(obj).__name__:
            if ch.isupper():
                table += '_'
            table += ch.lower()
        return table

    @staticmethod
    def __where_clause(pers):
        clause = ""
        keys = pers['__key__']

        if type(keys) == list:
            for key in keys:
                clause = clause + "%s = '%s' AND " % (key, pers[key])
            else:
                clause = clause[:-5]
        else:
            clause = "%s = '%s'" % (keys, pers[keys])

        return clause
