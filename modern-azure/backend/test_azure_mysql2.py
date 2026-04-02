import sqlalchemy
import certifi
import urllib.parse
ca_path = urllib.parse.quote_plus(certifi.where())
def test():
    try:
        e = sqlalchemy.create_engine(
            f'mysql+pymysql://docadmin:Nithilan%402006@doclynk-db.mysql.database.azure.com:3306/doclynkdb?ssl_ca={ca_path}'
        )
        res = e.connect().execute(sqlalchemy.text('SELECT 1')).fetchone()
        print("SUCCESS URL STRING STRATEGY:", res)
    except Exception as ex:
        print("ERROR URL STRING STRATEGY:", type(ex).__name__, ex)

test()
