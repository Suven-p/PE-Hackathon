from peewee import DatabaseProxy, PostgresqlDatabase


def is_postgres(db):
    if isinstance(db, DatabaseProxy):
        return isinstance(db.obj, PostgresqlDatabase)
    return isinstance(db, PostgresqlDatabase)
