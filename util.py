from configparser import ConfigParser
from pathlib import Path
from tkinter import Tk, filedialog
import unicodedata


class DirNotFoundError(Exception):
    pass


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


def select_html_file(initial_dir=''):
    """Select an HTML file through a dialog box.

    Parameters
    ----------
    initial_dir : str or pathlib.Path
        The directory that the dialog starts in.

    Returns
    -------
    file_path : pathlib.Path
        Path of the selected file. If the user clicks on the
        Cancel button, the returned value is `Path('.')`.
    """
    try:
        initial_dir = Path(initial_dir)
        if not initial_dir.is_dir():
            raise DirNotFoundError
    except (TypeError, DirNotFoundError):
        initial_dir = Path(__file__)
    
    title = 'Select workshop grades report HTML file'
    filetypes = [('HTML', '*.html;*.htm'), ('All files', '*.*')]
    file_str = filedialog.askopenfilename(
        initialdir=initial_dir,
        title=title,
        filetypes = filetypes,
    )
    file_path = Path(file_str)
    return file_path



class DataFolderManager:
    """Manage selection and persistence of a user-defined data folder.

    This class provides a simple mechanism to retrieve, store,
    and reuse a directory path chosen by the user. It attempts
    to read the folder path from a configuration file; if the path
    is missing or invalid, the user is prompted via a GUI dialog
    to select a folder. The chosen path is then saved to the
    configuration file for future sessions.

    Parameters
    ----------
    config_file : str or pathlib.Path-like
        Path to the configuration file where the selected folder
        will be stored.
    section : str
        Name of the configuration section containing the folder key.
    key : str
        Key under which the folder path is stored in the
        configuration file.

    Attributes
    ----------
    config_file : pathlib.Path
        Configuration file path as a :class:`~pathlib.Path` object.
    section : str
        Configuration section name.
    key : str
        Configuration key corresponding to the stored folder path.
    default_path : pathlib.Path
        Default directory used when no valid path is found in the
        configuration file. Defaults to the current working directory.
    _data_folder : pathlib.Path or None
        Cached folder path once resolved.

    Notes
    -----
    The folder selection dialog is implemented using :mod:`tkinter`.
    If the user cancels the dialog, a fallback path (either the
    previously stored folder or ``default_path``) is used.
    """

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
                pass # !!! Improve this
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
        # !!! None shouldn't be an option
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

