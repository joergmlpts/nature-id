#!/usr/bin/env python3

import numpy as np
from PIL import Image, ImageOps
import csv, sys, os, time
import inat_taxonomy

try:
    # try importing TensorFlow Lite first
    import tflite_runtime.interpreter as tflite
except Exception:
    try:
        # TensorFlow Lite not found, try to import full TensorFlow
        import tensorflow.lite as tflite
    except Exception:
        print('Error: TensorFlow Lite could not be loaded.', file=sys.stderr)
        print('       Follow instructions at https://www.tensorflow.org/lite/'
              'guide/python to install it.', file=sys.stderr)
        sys.exit(1)

# The directory where this Python script is located.
INSTALL_DIR = inat_taxonomy.INSTALL_DIR

# This directory contains models, label files, and taxonomy files.
CLASSIFIER_DIRECTORY = os.path.join(INSTALL_DIR, 'classifiers')

# These flags can be modified with command-line options.
scientific_names_only    = False # only scientific names or also common names
label_probabilities_only = False # probabilities for labels or hierarchical
all_common_names         = False # show only one or all common names
result_sz                = 5     # result size (for label_probabilities_only)

# This class is used by class Taxonomy.
class Taxon:

    def __init__(self, taxon_id):
        self.taxon_id = taxon_id  # for internal lookups and iNat API calls
        self.rank_level = None    # taxonomic rank, e.g. species, genus, family
        self.name = None          # scientific name
        self.common_name = None   # common name or None
        self.children = []        # list of child taxa
        self.leaf_class_ids = []  # list of indices into probabilities; there
                                  # can be more than one when we use old models
                                  # whose taxa have since been lumped together

    def add_child(self, child_taxon):
        self.children.append(child_taxon)

    # get taxonomic rank as a string
    def get_rank(self):
        if self.taxon_id < 0: # pseudo-kingdom?
            assert self.rank_level == inat_taxonomy.KINGDOM_RANK_LEVEL
            return ''
        return inat_taxonomy.get_rank_name(self.rank_level)

    # get the name to display; customize here to show common names differently
    def get_name(self):
        if self.common_name:
            return f'{self.common_name} ({self.name})'
        else:
            return self.name


# This taxonomy is represented in terms of instances of class Taxon.
class Taxonomy:

    def __init__(self):
        # The taxonomy file may contain multiple trees, one for each kingdom.
        # In order to have a single tree for prediction, we add a node for
        # Life as the parent of all kingdoms. This will be the root of our tree.
        self.root = Taxon(inat_taxonomy.ROOT_TAXON_ID)
        self.root.name = inat_taxonomy.ROOT_NAME
        self.root.rank_level = inat_taxonomy.ROOT_RANK_LEVEL
        self.id2taxon = { self.root.taxon_id : self.root }
        self.idx2label = {}

    def reset(self):
        self.root.children = []
        self.id2taxon = { self.root.taxon_id : self.root }
        self.idx2label = {}

    def taxonomy_available(self):
        return len(self.root.children) > 0

    def read_taxonomy(self, filename):
        tim = time.time()
        self.reset()
        with open(filename, newline='', encoding='latin-1') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'id' in row: # this is a label file
                    self.idx2label[int(row['id'])] = row['name']
                    continue

                taxon_id = int(row['taxon_id'])
                if taxon_id in self.id2taxon:
                    taxon = self.id2taxon[taxon_id] # inserted earlier as parent
                else:
                    self.id2taxon[taxon_id] = taxon = Taxon(taxon_id)

                taxon.name = row['name']
                if row['rank_level'].isdigit():
                    taxon.rank_level = int(row['rank_level'])
                else:
                    taxon.rank_level = float(row['rank_level'])

                if len(row['leaf_class_id']):
                    for leaf_class_id in row['leaf_class_id'].split(';'):
                        leaf_class_id = int(leaf_class_id)
                        taxon.leaf_class_ids.append(leaf_class_id)
                        self.idx2label[leaf_class_id] = taxon.name

                if len(row['parent_taxon_id']):
                    parent_taxon_id = int(row['parent_taxon_id'])
                else:
                    parent_taxon_id = self.root.taxon_id
                if not parent_taxon_id in self.id2taxon:
                    self.id2taxon[parent_taxon_id] = Taxon(parent_taxon_id)

                self.id2taxon[parent_taxon_id].add_child(taxon)

        if not self.taxonomy_available():
            # We parsed a label file; unless told otherwise, we use these
            # labels to build a taxonomic tree.
            print("Read %d labels from '%s' in %.1f secs." %
                  (len(self.idx2label), filename, time.time() - tim))

            if not label_probabilities_only:
                self.compute_taxonomic_tree()
                if self.taxonomy_available():
                    self.write_taxonomic_tree(filename.replace('labelmap',
                                                               'taxonomy'))
        else:
            print("Read taxonomy from '%s' in %.1f secs: %d taxa including %d "
                  "leaf taxa." % (filename, time.time() - tim,
                                  len(self.id2taxon) - 1, len(self.idx2label)))

        if not scientific_names_only and self.taxonomy_available():
            inat_taxonomy.annotate_common_names(self.id2taxon, all_common_names)
            if label_probabilities_only:
                self.annotate_labels_with_common_names()
        del self.id2taxon # not needed anymore

    # augment labels with common names
    def annotate_labels_with_common_names(self):
        for taxon in self.id2taxon.values():
            for leaf_class_id in taxon.leaf_class_ids:
                self.idx2label[leaf_class_id] = taxon.get_name()

    # write one row to taxonomy file
    def write_row(self, writer, taxon, parent_taxon_id):
        writer.writerow([parent_taxon_id, taxon.taxon_id, taxon.rank_level,
                         ';'.join([str(id) for id in taxon.leaf_class_ids]),
                         taxon.name])
        for child in taxon.children:
            self.write_row(writer, child, taxon.taxon_id)

    # write taxonomy file
    def write_taxonomic_tree(self, filename):
        try:
            with open(filename, 'w', newline='', encoding='latin-1') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['parent_taxon_id', 'taxon_id', 'rank_level',
                                 'leaf_class_id', 'name'])
                for child in self.root.children:
                    self.write_row(writer, child, '')
            print(f"Taxonomy written to file '{filename}'.")
        except Exception as e:
            print(f"Failure writing taxonomy to file '{filename}':", str(e))
            try:
                os.remove(filename)
            except Exception:
                pass

    # Called after loading label file for Google's AIY Vision Kit.
    # Adds all the labels' direct and indirect ancestors to compute
    # the taxonomic tree.
    def compute_taxonomic_tree(self):
        global label_probabilities_only
        if not inat_taxonomy.load_inat_taxonomy():
            label_probabilities_only = True
            return

        tim = time.time()
        IDX_ID         = inat_taxonomy.IDX_ID
        IDX_NAME       = inat_taxonomy.IDX_NAME
        IDX_RANK_LEVEL = inat_taxonomy.IDX_RANK_LEVEL
        new_id = 0   # id's we add on the fly for pseudo-kingdoms

        for idx, name in self.idx2label.items():
            inat_taxa = inat_taxonomy.lookup_id(name)
            if not inat_taxa:
                print(f"Info: Taxon for label '{name}' not found, "
                      "inserting as pseudo-kingdom.")
                new_id -= 1
                taxon_id = new_id
                self.id2taxon[taxon_id] = taxon = Taxon(taxon_id)
                taxon.rank_level = inat_taxonomy.KINGDOM_RANK_LEVEL
                taxon.name = name
                taxon.leaf_class_ids = [idx]
                self.root.add_child(taxon)
                continue

            inat_taxon, ancestors = inat_taxa
            if name != inat_taxon[IDX_NAME]:
                print(f"Info: Taxon '{name}' changed to "
                      f"'{inat_taxon[IDX_NAME]}', iNat taxa "
                      f"id {inat_taxon[IDX_ID]}.")

            # ancestor taxa
            prev_ancestor = self.root
            for ancestor in ancestors:
                id, parent_id, name, rank_level = ancestor
                if id in self.id2taxon:
                    prev_ancestor = self.id2taxon[id]
                else:
                    self.id2taxon[id] = ancestor_taxon = Taxon(id)
                    ancestor_taxon.name = name
                    ancestor_taxon.rank_level = rank_level
                    prev_ancestor.add_child(ancestor_taxon)
                    prev_ancestor = ancestor_taxon

            # this taxon
            id, parent_id, name, rank_level = inat_taxon
            if id in self.id2taxon:
                taxon = self.id2taxon[id]
                assert taxon.name == name
                assert taxon.rank_level == rank_level
            else:
                self.id2taxon[id] = taxon = Taxon(id)
                taxon.name = name
                taxon.rank_level = rank_level
                prev_ancestor.add_child(taxon)
            taxon.leaf_class_ids.append(idx)

        print('Computed taxonomic tree from labels in %.1f secs: '
              '%d taxa including %d leaf taxa.' %
              (time.time() - tim, len(self.id2taxon) - 1, len(self.idx2label)))

    # propagate probabilities to taxon and all below
    def assign_scores(self, taxon, probabilities):
        taxon.score = 0.0
        for leaf_class_id in taxon.leaf_class_ids:
            taxon.score += probabilities[leaf_class_id]
        for child in taxon.children:
            self.assign_scores(child, probabilities)
            taxon.score += child.score

    # Returns list of 5-tuples (probability, taxon_id, taxonomic rank,
    # scientific name, common name) ordered by taxonomic rank from kingdom
    # down to e.g. species.
    # Returns pairs (probability, scientific name) if label_probabilities_only
    # is set.
    def prediction(self, probabilities):

        if label_probabilities_only:
            # return list of pairs (probability, scientific name)
            total = np.sum(probabilities)
            indices = np.argpartition(probabilities, -result_sz)[-result_sz:]
            results = [(probabilities[i] / total, self.idx2label[i])
                       for i in indices if probabilities[i] != 0]
            results.sort(reverse=True)
            return results

        # annotate all taxa across the hierarchy with probabilities.
        self.assign_scores(self.root, probabilities)

        # return one hierarchical path guided by probabilities
        path = []
        taxon = self.root
        while taxon.children:
            # Find child with highest score.
            best_child = None
            for child in taxon.children:
                if not best_child or child.score > best_child.score:
                    best_child = child

            # Truncate path if all the other children combined are better
            if best_child.score < 0.5 * taxon.score:
                break

            path.append((best_child.score / self.root.score,
                         best_child.taxon_id, best_child.get_rank(),
                         best_child.get_name()))

            taxon = best_child

        return path

#
# Offline image classification.
#

class OfflineClassifier:

    def __init__(self, filenames):
        # Load TFLite model and allocate tensors.
        self.mInterpreter = tflite.Interpreter(model_path=filenames[0])
        self.mInterpreter.allocate_tensors()

        # Get input and output tensors.
        self.mInput_details = self.mInterpreter.get_input_details()
        self.mOutput_details = self.mInterpreter.get_output_details()

        # Read labels or taxonomy
        self.mTaxonomy = Taxonomy()
        self.mTaxonomy.read_taxonomy(filenames[1])

    def classify_image(self, image_filename):
        tim = time.time()
        try:
            img = Image.open(image_filename)
        except:
            print("Error: cannot load image '%s'." % image_filename)
            return []

        if img.mode != 'RGB':
            print("Error: image '%s' is of mode '%s', only mode RGB is "
                  "supported." % (image_filename, img.mode))
            return []

        # rotate image if needed as it may contain EXIF orientation tag
        img = ImageOps.exif_transpose(img)

        model_size = tuple(self.mInput_details[0]['shape'][1:3])

        # square target shape expected by crop code below
        assert model_size[0] == model_size[1]

        if img.size != model_size:
            # We need to scale and maybe want to crop image.
            width, height = img.size
            if width != height:
                # Before scaling, we crop image to square shape.
                left = 0
                right = width
                top = 0
                bottom = height
                if width < height:
                    top = (height - width) / 2
                    bottom = top + width
                else:
                    left = (width - height) / 2
                    right = left + height
                img = img.crop((left, top, right, bottom))

            # scale image
            img = img.resize(model_size)

        #img.show()

        # pixels are in range 0 ... 255, turn into numpy array
        input_data = np.array([np.array(img, self.mInput_details[0]['dtype'])])

        if self.mInput_details[0]['dtype'] == np.float32:
            # normalize floats to range -1.0 ... 1.0
            input_data -= 128.0
            input_data /= 128

        self.mInterpreter.set_tensor(self.mInput_details[0]['index'],
                                     input_data)
        self.mInterpreter.invoke()

        output_data = self.mInterpreter.get_tensor(self.mOutput_details[0]
                                                   ['index'])
        path = self.mTaxonomy.prediction(output_data[0])
        print("\nClassification of '%s' took %.1f secs." %
              (image_filename, time.time() - tim))
        return path

# Returns a dictionary that maps available classifiers to a pair of filenames.
def get_installed_models():

    if not os.path.isdir(CLASSIFIER_DIRECTORY):
        print("Cannot load classifiers, directory "
              f"'{CLASSIFIER_DIRECTORY}' does not exist.")
        sys.exit(1)

    choices = [ 'birds', 'insects', 'plants']
    models = {}

    for filename in os.listdir(CLASSIFIER_DIRECTORY):
        model = None
        if filename.endswith(".csv"):
            if filename == 'taxonomy.csv':
                model = 'Seek'
            else:
                for m in choices:
                    if filename.find(m) != -1:
                        model = m
                        break
            if model:
                filename = os.path.join(CLASSIFIER_DIRECTORY, filename)
                if model in models:
                    if not models[model][1] or models[model][1].\
                       endswith('labelmap.csv'):
                        models[model] = (models[model][0], filename)
                else:
                    models[model] = (None, filename)
        elif filename.endswith(".tflite"):
            if filename == 'optimized_model.tflite':
                model = 'Seek'
            else:
                for m in choices:
                    if filename.find(m) != -1:
                        model = m
                        break
            if model:
                filename = os.path.join(CLASSIFIER_DIRECTORY, filename)
                if model in models:
                    models[model] = (filename, models[model][1])
                else:
                    models[model] = (filename, None)

    delete_elements = [] # postponed deletion, cannot delete during iteration
    for name, files in models.items():
        if not files[0] or not files[1]:
            print("Installation issue: Excluding incomplete classifier for"
                  " '%s': %s." % (name, ".csv file but no .tflite file"
                  if files[1] else ".tflite file but no .csv file"))
            delete_elements.append(name)

    for element in delete_elements:
        del models[element]

    if not models:
        print(f"No classifiers found in directory '{CLASSIFIER_DIRECTORY}'; "
              "follow instructions in "
              f"'{os.path.join(CLASSIFIER_DIRECTORY,'README.md')}'"
              " to install them.", file=sys.stderr)
        sys.exit(1)
    return models

def identify_species(classifier, filename):
    result = classifier.classify_image(filename)
    if result:
        # Print list of tuples (probability, taxon id, taxonomic rank, name)
        # ordered by taxonomic rank from kingdom down to species.
        for entry in result:
            if len(entry) == 2: # labels only
                print('%5.1f%% %s' % (100 * entry[0], entry[1]))
                continue
            print('%5.1f%% %11s %s' % (100 * entry[0], entry[2], entry[3]))

# command-line parsing

models = get_installed_models()

def model_parameter_check(arg):
    if not arg in models:
        s = '' if len(models) == 1 else 's'
        msg = f"Model '{arg}' not available. Available model{s}:"
        prefix = ' '
        for m in models:
            msg += f"{prefix}'{m}'"
            prefix = ', '
        msg += '.'
        raise argparse.ArgumentTypeError(msg)
    return arg

def result_size_check(arg):
    if arg.isdigit() and int(arg) > 0 and int(arg) <= 100:
        return int(arg)
    raise argparse.ArgumentTypeError(f"'{arg}' is not a number "
                                     "between 1 and 100.")

def file_directory_check(arg):
    if os.path.isdir(arg) or os.path.isfile(arg):
        return arg
    raise argparse.ArgumentTypeError(f"'{arg}' is not a file or directory.")

#
# Identify species for picture files and directories given as command line args
#

if __name__ == '__main__':
    import argparse

    # For Ubuntu 18.04 where stdout has not been opened for Unicode.
    sys.stdout = open(sys.stdout.fileno(), mode='w',
                      encoding='utf8', buffering=1)

    preferred = 'Seek' # default if this model is available

    parser = argparse.ArgumentParser()
    if len(models) == 1 or preferred in models:
        default_model = next(iter(models)) if len(models) == 1 else preferred
        parser.add_argument("-m", "--model", type=model_parameter_check,
                            default=default_model,
                            help="Model to load to identify lifeforms.")
    else: # no default for classification model
        parser.add_argument("-m", "--model", type=model_parameter_check,
                            required=True,
                            help="Model to load to identify lifeforms.")
    parser.add_argument('-a', '--all_common_names', action="store_true",
                        help='Show all common names and not just one.')
    parser.add_argument('-l', '--label_probabilities_only', action="store_true",
                        help='Compute and display only label probabilities, '
                        'do not propagate probabilities across the hierachy.')
    parser.add_argument('-s', '--scientific_names_only', action="store_true",
                        help='Only use scientific names, do not load common '
                        'names.')
    parser.add_argument('-r', '--result_size', type=result_size_check,
                        default=result_sz, help='Number of labels and their '
                        'probabilities to report in results.')
    parser.add_argument('files_dirs', metavar='file/directory',
                        type=file_directory_check, nargs='+',
                        help='Image files or directories with images.')
    args = parser.parse_args()

    scientific_names_only = args.scientific_names_only
    label_probabilities_only = args.label_probabilities_only
    all_common_names = args.all_common_names
    result_sz = args.result_size

    # make classifier instance

    classifier = OfflineClassifier(models[args.model])

    # process photos

    for arg in args.files_dirs:
        if os.path.isfile(arg):
            identify_species(classifier, arg)
        elif os.path.isdir(arg):
            for file in os.listdir(arg):
                ext = os.path.splitext(file)[1].lower()
                if ext in ['.jpg', '.jepg', '.png']:
                    identify_species(classifier, os.path.join(arg, file))
