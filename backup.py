import shutil
from datetime import datetime
from pathlib import Path

origem = Path("instance/agendamento.db")
pasta = Path("backups")
pasta.mkdir(exist_ok=True)

data = datetime.now().strftime("%Y%m%d_%H%M%S")
destino = pasta / f"agendamento_{data}.db"

shutil.copy2(origem, destino)

print(f"Backup criado: {destino}")