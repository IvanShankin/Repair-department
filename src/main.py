import asyncio

from src.service.config.core import get_config, init_conf
from src.database.core import init_db
from src.database.filling import filling_db
from src.service.utils.core_logger import setup_logging
from src.ui.main_ui import RepairApp


async def main():
    init_conf()
    setup_logging(get_config().log_file)
    await init_db()

    await filling_db()

    RepairApp().run()


if __name__ == "__main__":
    asyncio.run(main())