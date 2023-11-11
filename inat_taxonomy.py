import csv, sys, os, time, locale, zipfile, io
import inat_api
from dataclasses import dataclass
from typing import List, Dict

# The directory where this Python script is located.
INSTALL_DIR = os.path.dirname(__file__)
while os.path.islink(INSTALL_DIR):
    INSTALL_DIR = os.path.join(INSTALL_DIR,
                               os.path.dirname(os.readlink(INSTALL_DIR)))

# This zip file contains the taxonomy and all common names.
# Download https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip and
# leave this zip file in directory 'inaturalist-taxonomy'. Do not extract the
# files from this zip archive.
INAT_TAXONOMY = os.path.join(INSTALL_DIR, 'inaturalist-taxonomy',
                             'inaturalist-taxonomy.dwca.zip')

# A special node represents the root of the tree, the parent of kingdoms.
ROOT_TAXON_ID   = 48460
ROOT_NAME       = 'Life'
ROOT_RANK_LEVEL = 100

# maps rank-level to its name
gRankLevel2Name = {
     ROOT_RANK_LEVEL : 'stateofmatter', # used for the parent of kingdoms
      70  : 'kingdom',
      67  : 'subkingdom',
      60  : 'phylum',
      57  : 'subphylum',
      53  : 'superclass',
      50  : 'class',
      47  : 'subclass',
      45  : 'infraclass',
      44  : 'subterclass',
      43  : 'superorder',
      40  : 'order',
      37  : 'suborder',
      35  : 'infraorder',
      34.5: 'parvorder',
      34  : 'zoosection',
      33.5: 'zoosubsection',
      33  : 'superfamily',
      32  : 'epifamily',
      30  : 'family',
      27  : 'subfamily',
      26  : 'supertribe',
      25  : 'tribe',
      24  : 'subtribe',
      20  : 'genus',
      19  : 'genushybrid', # changed, was same as genus in iNaturalist
      15  : 'subgenus',
      13  : 'section',
      12  : 'subsection',
      11  : 'complex',
      10  : 'species',
       9  : 'hybrid',      # changed, was same as species in iNaturalist
       5  : 'subspecies',
       4  : 'variety',     # changed, was same as subspecies in iNaturalist
       3  : 'form',        # changed, was same as subspecies in iNaturalist
       2  : 'infrahybrid'  # changed, was same as subspecies in iNaturalist
}

# maps rank name to numeric rank-level
gName2RankLevel = {}
for key, value in gRankLevel2Name.items():
    gName2RankLevel[value] = key

KINGDOM_RANK_LEVEL = gName2RankLevel['kingdom']

def get_rank_level(rank):
    assert rank in gName2RankLevel
    return gName2RankLevel[rank]

def get_rank_name(rank_level, default_name = 'clade'):
    return gRankLevel2Name[rank_level] if rank_level in gRankLevel2Name \
           else default_name

@dataclass(frozen=True)
class Taxon:
    id        : int
    parent_id : int
    name      : str
    rank_level: float

# iNaturalist taxa, only loaded when a taxonomic tree needs
# to be computed from a label file.

gName2Taxa: Dict[str,List[Taxon]] = {}
"maps taxon name to list of taxa"

gId2Taxon: Dict[int,Taxon]        = {}
"maps taxon id to taxon"

def load_inat_taxonomy():
    "Load all iNaturalist taxa from file 'taxa.csv'."
    global gName2Taxa
    global gId2Taxon

    if gName2Taxa and gId2Taxon:
        return True # already loaded

    print('Loading iNaturalist taxonomy...')
    start_time = time.time()
    gName2Taxa = {}
    gId2Taxon = {}

    try:
        with zipfile.ZipFile(INAT_TAXONOMY, 'r') as zf:
            with zf.open('taxa.csv', 'r') as zfile:
                with io.TextIOWrapper(zfile, encoding = 'latin-1') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        id = int(row['id'])
                        parent_id = row['parentNameUsageID'].split('/')[-1]
                        parent_id = int(parent_id) if parent_id else \
                                 ROOT_TAXON_ID if id != ROOT_TAXON_ID else None
                        name = row['scientificName']
                        rank = row['taxonRank']
                        if not rank in gName2RankLevel:
                            response = inat_api.get_taxa_by_id(id)
                            if response and 'results' in response:
                                rank_level = response['results'][0]\
                                                     ['rank_level']
                                gName2RankLevel[rank] = rank_level
                                if not rank_level in gRankLevel2Name:
                                    gRankLevel2Name[rank_level] = rank
                                print(f"Please add rank '{rank}' to gName2Rank"
                                      f"Level, numeric value {rank_level}.")
                            else:
                                gName2RankLevel[rank] = -1
                        rank_level = gName2RankLevel[rank]
                        inat_taxon = Taxon(id, parent_id, name, rank_level)
                        if name in gName2Taxa:
                            gName2Taxa[name].append(inat_taxon)
                        else:
                            gName2Taxa[name] = [inat_taxon]
                        assert not id in gId2Taxon
                        gId2Taxon[id] = inat_taxon
                        if len(gId2Taxon) % 10000 == 0:
                            print(f' {len(gId2Taxon):,} ' if len(gId2Taxon) %
                                  100000 == 0 else '.', end='')
                            sys.stdout.flush()

        assert ROOT_TAXON_ID in gId2Taxon
        print(f' {len(gId2Taxon):,}.')
        print(f'Loaded iNaturalist taxonomy of {len(gId2Taxon):,} taxa '
              f'in {time.time()-start_time:.1f} secs.')
        return True

    except Exception as e:
        print("Cannot load taxonomy 'taxa.csv' from archive "
              f"'{INAT_TAXONOMY}': {str(e)}.")
        gName2Taxa = {}
        gId2Taxon = {}
        return False

def beautify_common_name(name):
    "Capitalize (most) words in common name; helper function for common names."
    if name.endswith(' [paraphyletic]'):
        name = name[:-15] # fix dicots
    name =  '-'.join(word[0].upper() + word[1:]
                     for word in name.split('-'))
    return ' '.join(word if word == 'and' or word.endswith('.')
                    else word[0].upper() + word[1:]
                    for word in name.split())

def annotate_common_names(id2taxon, all_common_names = False):
    """
    Load the common names in our language, annotate taxonomic tree with them.
    The parameter `id2taxon' includes the taxa we are interested in.
    """
    start_time = time.time()
    language, _ = locale.getdefaultlocale()

    if language in ['C', 'C.UTF-8', 'POSIX']:
        language = 'en'

    if not os.path.isfile(INAT_TAXONOMY):
        print("Cannot load common names, archive "
              f"'{INAT_TAXONOMY}' does not exist.")
        return

    try:
        with zipfile.ZipFile(INAT_TAXONOMY, 'r') as zf:
            perfect_match = []
            other_matches = []

            # check all common names files for names in our language
            for fname in zf.namelist():
                if fname.startswith("VernacularNames-") and \
                   fname.endswith(".csv"):
                    with zf.open(fname, 'r') as zfile:
                        with io.TextIOWrapper(zfile, encoding='utf-8') as csvf:
                            reader = csv.DictReader(csvf)
                            for row in reader:
                                lang = row['language']
                                if lang == language:
                                    perfect_match.append(fname)  # en vs en
                                elif len(lang) < len(language) and \
                                     lang == language[:len(lang)]:
                                    other_matches.append(fname)  # en vs en_US
                                break

            if not perfect_match and not other_matches:
                print("Cannot find common names for language '{language}'.")
                return

            # annotate the taxa with common names
            total_names = loaded_names = 0
            for fname in perfect_match + other_matches:
                print(f"Reading common names from '{INAT_TAXONOMY}' "
                      f"member '{fname}'...")
                with zf.open(fname, 'r') as zfile:
                    with io.TextIOWrapper(zfile, encoding='utf-8') as csvf:
                        reader = csv.DictReader(csvf)
                        for row in reader:
                            total_names += 1
                            id = int(row['id'])
                            if id in id2taxon and (all_common_names or \
                                            id2taxon[id].common_name is None):
                                loaded_names += 1
                                cname = beautify_common_name(row['vernacular'
                                                                 'Name'])
                                if id2taxon[id].common_name is None:
                                    id2taxon[id].common_name = cname
                                else:
                                    id2taxon[id].common_name += '; ' + cname

        print(f'Read {total_names:,} common names in '
              f'{time.time()-start_time:.1f} secs, loaded {loaded_names:,} '
              f'in language "{language}" for {len(id2taxon)-1:,} taxa.')

    except Exception as e:
        print(f"Cannot load common names from archive '{INAT_TAXONOMY}':"
              f" {str(e)}.")

def get_ancestors(id, ancestors):
    """
    Ancestors are a list of instances of Taxon; they are ordered from the
    kingdom down.
    """
    taxon = gId2Taxon[id]
    if taxon.rank_level < KINGDOM_RANK_LEVEL:
        get_ancestors(taxon.parent_id, ancestors)
    ancestors.append(taxon)

def lookup_id(name, desired_ranks = ['species', 'subspecies']):
    """
    Lookup by name, returns a pair, a Taxon and its ancestors, a list of
    Taxon. Desired_ranks are returned in case of ambiguities (duplicate names).
    """
    if not gName2Taxa:
        return None # taxonomy not loaded
    if name in gName2Taxa:
        taxa = gName2Taxa[name]
        if len(taxa) > 1:
            species = None
            subspecies = None
            print(f"Warning: multiple taxa named '{name}':", end='')
            prefix = ' '
            taxon = None
            for t in taxa:
                rank = get_rank_name(t.rank_level)
                print(f"{prefix}{rank} {t.id}", end='')
                if rank in desired_ranks:
                    taxon = t
                prefix = ', '
            if not taxon:
                taxon = taxa[0]
            rank = get_rank_name(taxon.rank_level)
            print(f"; choosing {rank}.")
        else:
            taxon = taxa[0]
        ancestors = []
        if taxon.rank_level < KINGDOM_RANK_LEVEL:
            get_ancestors(taxon.parent_id, ancestors)
        return (taxon, ancestors)
    else:
        # likely taxon change, query iNat API
        response = inat_api.get_taxa({ 'q'         : name,
                                       'all_names' : 'true',
                                       'per_page'  : 200 })
        if not response:
            print(f"API lookup for name '{name}' failed.")
            return
        taxa = response['results']
        if len(taxa) > 1:
            # more than one taxon, find the one that used to have this name
            exact_matches = [taxon for taxon in taxa for nam in taxon['names']
                             if nam['locale'] == 'sci' and nam['name'] == name]
            if exact_matches:
                taxa = exact_matches
        ids = [taxon['id'] for taxon in taxa]
        taxa = set([gId2Taxon[id] for id in ids if id in gId2Taxon])
        if not taxa:
            return
        while len(taxa) > 1:
            # multiple taxa, find their common ancestor
            min_rank_level = min([taxon.rank_level for taxon in taxa])
            new_taxa = set()
            for taxon in taxa:
                new_taxon = gId2Taxon[taxon.parent_id] \
                              if taxon.rank_level == min_rank_level \
                              else taxon
                if not new_taxon in new_taxa:
                    new_taxa.add(new_taxon)
            taxa = new_taxa
        taxon = taxa.pop()
        ancestors = []
        if taxon.rank_level < KINGDOM_RANK_LEVEL:
            get_ancestors(taxon.parent_id, ancestors)
        return (taxon, ancestors)


if __name__ == '__main__':

    assert not 'Not a top-level Python module!'
