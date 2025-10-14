import logging


def setup_logging() -> None:
    """
    Configure basic logging formatting for the application.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s,%(msecs)03d | %(levelname)-8s | %(name)s | %(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
