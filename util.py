from configparser import ConfigParser
from pathlib import Path
from tkinter import Tk, filedialog
import unicodedata


def normalize(text):
    """
    Remove accents from a string and convert to lowercase.

    Helper function for sorting strings in a way that ignores
    diacritical marks (accents) and case.

    Parameters
    ----------
    text : str
        The input string to normalize.

    Returns
    -------
    str
        A normalized version of the input string without accents, 
        converted to lowercase.

    Examples
    --------
    >>> normalize('Ángel Fernández Peña')
    'angel fernandez pena'
    
    >>> names = ['ángel', 'Marta', 'Óscar', 'María', 'Elena', 'ana']
    >>> sorted(names)  # Unicode order (not what we want)
    ['Elena', 'Marta', 'María', 'ana', 'Óscar', 'ángel']
    >>> sorted(names, key=normalize)  # Normalized order
    ['ana', 'ángel', 'Elena', 'María', 'Marta', 'Óscar']
    """
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).lower()



class DataFolderManager:
    def __init__(self, config_file, section, key):
        self.config_file = Path(config_file)
        self.section = section
        self.key = key
        self.default_path = Path.cwd()
        self._data_folder = None

    def load_from_config(self):
        """Load data folder from config file if available."""
        if self.config_file.exists():
            config = ConfigParser()
            config.read(self.config_file)
            try:
                folder = Path(config[self.section][self.key])
                if folder.exists():
                    return folder
            except KeyError:
                pass
        return self.default_path

    def save_to_config(self, path):
        """Save the selected data folder to the config file."""
        config = ConfigParser()
        config[self.section] = {self.key: str(path)}
        with open(self.config_file, 'w') as f: # !!! Check this
            config.write(f)

    def prompt_for_folder(self, initial_dir=None):
        """Open GUI dialog to let the user choose a folder."""
        initial_dir = str(initial_dir or self.default_path)
        root = Tk()
        root.withdraw()
        folder_selected = filedialog.askdirectory(
            title="Select Data Folder", initialdir=initial_dir
        )
        root.destroy()
        return Path(folder_selected) if folder_selected else None

    def get_data_folder(self):
        """Main method to retrieve or prompt for the data folder."""
        if self._data_folder is not None:
            return self._data_folder
        
        initial = self.load_from_config()
        folder = self.prompt_for_folder(initial)
        if folder:
            self.save_to_config(folder)
            self._data_folder = folder
        else:
            print("No folder selected. Using fallback path.")
            self._data_folder = initial
        
        return self._data_folder

