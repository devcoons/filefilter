__version__ = "0.1.1"

from .config import Config
from .matcher import collect_files
import json


def filter_paths(config_json: str, resolve_base: str = 'cwd'):
    """
    Given a JSON string defining 'root_dir' and 'filters',
    returns a list of file paths matching the rules.

    Parameters:
      - config_json: JSON string with 'root_dir' and 'filters'
      - resolve_base: 'cwd' (default) to resolve root_dir relative to current working directory,
                      'script' to resolve relative to this library's script directory.
    """
    data = json.loads(config_json)
    cfg = Config(data, resolve_base=resolve_base)
    return collect_files(cfg)