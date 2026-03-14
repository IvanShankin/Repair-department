from src.database.core import init_db
from src.database.filling import filling_db
from src.service.config.core import get_config, init_conf
from src.service.utils.core_logger import setup_logging
from src.ui.main_ui import RepairApp


def main():
    init_conf()

    setup_logging(get_config().log_file)

    init_db()
    filling_db()

    RepairApp().run()


if __name__ == "__main__":
    main()
