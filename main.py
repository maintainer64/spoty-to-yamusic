import click
from sqlalchemy import create_engine
from models import Base  # Импортируйте Base из вашего модуля models
from config import DATABASE_URL  # Импортируйте DATABASE_URL из config.py
from logic import loop_forever, loop, add_task_album  # Импортируйте ваши функции

# Создайте engine для базы данных
_engine = create_engine(DATABASE_URL)


@click.group()
def cli():
    """CLI для управления задачами переноса альбомов."""
    pass


@cli.command()
def init():
    """Инициализирует базу данных и создаёт таблицы."""
    Base.metadata.create_all(_engine)
    click.echo("База данных инициализирована, таблицы созданы.")


@cli.command()
def loop():
    """Запускает фоновую задачу loop_forever."""
    click.echo("Запуск фоновой задачи loop_forever...")
    loop_forever()


@cli.command()
def bot():
    """Запускает один раз задачу loop."""
    click.echo("Запуск фоновой задачи bot...")
    from bot import main
    main()


if __name__ == "__main__":
    cli()
