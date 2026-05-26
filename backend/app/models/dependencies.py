# Adicione a importação de contextmanager
from contextlib import contextmanager
from sqlalchemy.orm import sessionmaker

# Mantenha a importação do seu 'db' (engine)
# Supondo que ele esteja em um arquivo 'database.py' ou 'models.py'
from backend.app.models.models import engine

# Adicione este decorador
@contextmanager
def pegar_sessao():
    # Sua lógica original está perfeita e não muda
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()