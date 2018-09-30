from abc import ABC, abstractmethod


class Connector(ABC):
    def __init__(self, host, db, user, pw, prefix):
        self.host = host
        self.db = db
        self.user = user
        self.pw = pw
        self.prefix = prefix

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def persist(self, conn, obj):
        pass

    @abstractmethod
    def discovery_query_for_object(self, obj):
        pass

    @abstractmethod
    def insert_query_for_object(self, obj):
        pass

    @abstractmethod
    def update_query_for_object(self, obj):
        pass

    @abstractmethod
    def execute_query(self, conn, query):
        pass

    @abstractmethod
    def next_sequence(self, conn, sequence):
        pass
