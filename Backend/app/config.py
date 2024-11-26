from urllib.parse import quote_plus

class Config:
    SQLALCHEMY_DATABASE_URI = (
        "mssql+pyodbc://sa:admin123@localhost/TechShop?driver=ODBC+Driver+17+for+SQL+Server"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Desactiva para evitar overhead
    SQLALCHEMY_ECHO = True  # Activa para ver las consultas SQL (opcional)
