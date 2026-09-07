import json
import logging
from pathlib import Path

# we must declare the logger first

logger = logging.getLogger(__name__)

class MalayNormalizer:

    def __init__(self, data_dir=None):

        # lets load our data_directories
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / 'data'
        else:
            self.data_dir = Path(data_dir)

        # load our normalizer

        # loading the all json
        
        self.root_mapping = self.load_json('root_mapping.json')
        
        self.stemming_exceptions = self.load_stemming_exception()

        # first we need to declare empty dict.
        self.form_to_root = {}

        for root, forms in self.root_mapping.items():
            for form in forms:
                self.form_to_root[form] = root

        try:
            from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
            self.stemmer = StemmerFactory().create_stemmer()
        except ImportError:
            logger.warning("Sastrawi not installed - skipping the stemming in topic cleaning")
            self.stemmer = None

        logger.info(f"😀 Loaded {len(self.root_mapping)} root word mapping for each verb")

    def load_json(self, filename):
        """Helper method"""
        file_path = self.data_dir / filename
        # handling missing file 
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"required file {filename} not found in {self.data_dir}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_stemming_exception(self):
        """load the stemming exception: word like perkembangan really important not kembang"""
        file_path = self.data_dir / 'stemming_exceptions.txt'
        stemming_exceptions_word = set()

        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            stemming_exceptions_word.add(line.lower())
        else:
            logger.warning(f"Stem Exceptions file not found {file_path}")

            stemming_exceptions_word = {
                'perkembangan', 'perubahan',
            }
        return stemming_exceptions_word

    def normalize(self, word):
        """we will call this function in another method """
        if not word or not word.strip():
            return word

        word = word.lower().strip()
        # and now we have dict of form_to_root
        #
        # check wether word also have in stemming exception
        if word in self.stemming_exceptions:
            return word

        if word in self.form_to_root:
            return self.form_to_root[word]
        else:
            return self.stemmer.stem(word) if self.stemmer else word

    




