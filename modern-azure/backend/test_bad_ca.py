import sqlalchemy
e = sqlalchemy.create_engine('mysql+pymysql://docadmin:Nithilan%402006@doclynk-db.mysql.database.azure.com:3306/doclynkdb', connect_args={'ssl': {'ca': 'doesnotexist.pem'}})
e.connect()
