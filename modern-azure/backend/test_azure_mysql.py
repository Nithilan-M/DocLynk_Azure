import sqlalchemy
import certifi

def test():
    try:
        e = sqlalchemy.create_engine(
            'mysql+pymysql://docadmin:Nithilan%402006@doclynk-db.mysql.database.azure.com:3306/doclynkdb',
            connect_args={'ssl': {'ca': certifi.where()}}
        )
        res = e.connect().execute(sqlalchemy.text('SELECT 1')).fetchone()
        print("SUCCESS:", res)
    except Exception as ex:
        print("ERROR:", type(ex).__name__, ex)

test()
