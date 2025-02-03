# seu_app/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from .tasks import salvar_relatorio_financeiro
import locale
locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(salvar_relatorio_financeiro, 'cron', day='last', hour=23, minute=59)
    scheduler.start()