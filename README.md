# Identify Plants, Birds, and Insects in Photos

This repository provides Python code that identifies plants, birds, and insects in photos.

This project was inspired by the amazing progress in identifying plants, animals and mushrooms in photos that has been made by [iNaturalist](https://iNaturalist.org) in recent years in identifying plants, animals, and fungi from photographs. The iNaturalist team has trained machine learning models with their large collection of photos and research-grade identifications. In 2019, iNaturalist released [Seek by iNaturalist](https://www.inaturalist.org/pages/seek_app) which identifies photos offline on the phone and identifies to a higher level than species when a species identification cannot be made.

Google provides three models that have been trained with iNaturalist data - classification models for plants, birds, and insects. These Google models can be downloaded and used with Google's `TensorFlow` and `TensorFlow Lite` tools.

This code is based on the trained models provided by Google. It was written to experiment with identifying species from photos and to try out Seek's approach to calculating scores (probabilities) across the taxonomic hierarchy.

This tool `nature_id.py` has been tested on Linux and Windows. It should also work on MacOS.

## Usage

This is a command-line tool. It is invoked with images or directories containing images and identifies the plants, birds, and insects in those images.

Here is an example. This is the command for Linux and macOS:

```
./nature_id.py -m plants plant_images/Persicaria_amphibia.jpg
```

On Windows the command is:

```
python .\nature_id.py -m plants plant_images\Persicaria_amphibia.jpg
```

![Smartweed](/plant_images/Persicaria_amphibia.jpg)

The above image results in this identification:
```
Classification of 'plant_images/Persicaria_amphibia.jpg' took 0.2 secs.
100.0%     kingdom Plants (Plantae)
100.0%      phylum Tracheophytes (Tracheophyta)
100.0%   subphylum Flowering Plants (Angiospermae)
 99.6%       class Dicots (Magnoliopsida)
 99.2%       order Pinks, Cactuses, and Allies (Caryophyllales)
 98.8%      family Knotweed Family (Polygonaceae)
 98.8%   subfamily Polygonoideae
 98.8%       tribe Persicarieae
 98.8%    subtribe Persicariinae
 98.8%       genus Smartweeds (Persicaria)
 97.6%     species Water Smartweed (Persicaria amphibia)
```

These scores can be used to guide identification: define a threshold and report as result the taxon with the lowest score that is larger than or equal to this threshold. In this example for a threshold of 95% an identification to species *Persicaria amphibia* has been achieved. For a threshold of 99%, this is only an identification to order *Caryophyllales*. 95% and 99% would be unusually high thresholds; Seek, I believe, uses a threshold of 70%.

## Command-line Options

This script is a command-line utility. It is called with options, filenames and directory names as arguments. These options are supported:

```
usage: nature_id.py [-h] [-m MODEL] [-a] [-l] [-s] [-r RESULT_SIZE] file/directory [file/directory ...]

positional arguments:
  file/directory        Image files or directories with images.

options:
  -h, --help            show this help message and exit
  -m MODEL, --model MODEL
                        Model to load to identify organisms.
  -a, --all_common_names
                        Show all common names and not just one.
  -l, --label_scores_only
                        Compute and display only label scores, do not propagate scores up the hierarchy.
  -s, --scientific_names_only
                        Only use scientific names, do not load common names.
  -r RESULT_SIZE, --result_size RESULT_SIZE
                        Number of labels and their scores to report in results.
```

### Option -m MODEL, --model MODEL

The `-m` and `--model` options select a classification model. Possible models are `plants`, `birds`, and `insects`. These models must be installed in the `classifiers` directory. This option is required if more than one classifier is installed.

###  Option -a, --all_common_names

The `-a` and `--all_common_names` options cause all common names to be displayed, not just one. Multiple common names are separated by semicolons. The output with this option looks like this:

![Phyla_nodiflora.jpg](/plant_images/Phyla_nodiflora.jpg)

```
Classification of 'plant_images/Phyla_nodiflora.jpg' took 0.2 secs.
100.0%     kingdom Plants; Flora; Green Plants; Greenery; Foliage; Vegetation; Salpichlaena Papyrus; Trees; Bushes; Shrubs; Vines (Plantae)
100.0%      phylum Tracheophytes; Seed Plants; Vascular Plants (Tracheophyta)
100.0%   subphylum Flowering Plants; Angiosperms; Flowers; Basal Angiosperms; True Dicotyledons; Basal True Dicots; Rose Dicots; Daisy Dicots (Angiospermae)
100.0%       class Dicots; Dicots; Dicotyledons; Eudicots (Magnoliopsida)
 98.2%       order Mints, Plantains, Olives, and Allies (Lamiales)
 97.4%      family Verbena Family; Lantanas (Verbenaceae)
 97.4%       tribe Lantaneae
 85.5%       genus Frogfruits; Fogfruits (Phyla)
 85.5%     species Turkey Tangle; Lippia; Common Lippia; Turkey Tangle Frogfruit; Sawtooth Fogfruit; Carpet Weed; Roundleaf Frogfruit; Texas Frogfruit; Cape Weed; Sawtooth Frogfruit; Lipia; Turkey Tangle Fogfruit; Daisy Lawn; Fog Grass (Phyla nodiflora)
```

### Option -l, --label_scores_only

The `-l` and `--label_scores_only` options switch from the taxonomic hierarchy view to a flat list of labels and their scores. The output with this option looks like this:

![Solidago_velutina_ssp_californica.jpg](/plant_images/Solidago_velutina_ssp_californica.jpg)

```
Classification of 'plant_images/Solidago_velutina_ssp_californica.jpg' took 0.2 secs.
 86.1% Canada Goldenrod (Solidago canadensis)
  9.8% Late Goldenrod (Solidago altissima)
  1.6% Flat-Topped Goldenrod (Euthamia graminifolia)
  1.2% Northern Seaside Goldenrod (Solidago sempervirens)
  0.4% Stiff-Leaved Goldenrod (Solidago rigida)
```

Five labels with decreasing scores are shown by default. The `-r` and `--result_size` options can be used to request fewer or more labels.

### Option -s, --scientific_names_only

The `-s` and `--scientific_names_only` options disable common names; only the scientific names are displayed.  The output with this option looks like this:

![Trichostema_lanceolatum.jpg](/plant_images/Trichostema_lanceolatum.jpg)

```
Classification of 'plant_images/Trichostema_lanceolatum.jpg' took 0.2 secs.
100.0%     kingdom Plantae
100.0%      phylum Tracheophyta
100.0%   subphylum Angiospermae
100.0%       class Magnoliopsida
 99.6%       order Lamiales
 99.6%      family Lamiaceae
 99.2%   subfamily Ajugoideae
 99.2%       genus Trichostema
 99.2%     species Trichostema lanceolatum
```

### Option -r RESULT_SIZE, --result_size RESULT_SIZE

The `-r` and `--result_size` options modify the number of labels displayed when a flat list of labels is requested with the `-l` or `--label_scores_only` options. The default is 5. Options `-r` and `--result_size` allow you to choose a number between 1 and 100.

This is an example with 15 labels. The command-line for Linux is
```
./nature_id.py -m plants -l -r 15 plant_images/Primula_hendersonii.jpg
```

![Primula_hendersonii.jpg](/plant_images/Primula_hendersonii.jpg) 

```
Classification of 'plant_images/Primula_hendersonii.jpg' took 0.2 secs.
 50.4% Henderson's Shooting Star (Primula hendersonii)
 37.2% Eastern Shooting Star (Primula meadia)
  2.5% Dark-Throated Shooting Star (Primula pauciflora)
  1.7% Red Ribbons (Clarkia concinna)
  1.2% Ruby Chalice Clarkia (Clarkia rubicunda)
  0.8% Purple Paintbrush (Castilleja purpurea)
  0.8% Fireweed (Chamaenerion angustifolium)
  0.4% Western Fairy-Slipper (Calypso bulbosa occidentalis)
  0.4% Texas Skeleton Plant (Lygodesmia texana)
  0.4% Rhodora (Rhododendron canadense)
  0.4% Ragged-Robin (Silene flos-cuculi)
  0.4% Hemp Dogbane (Apocynum cannabinum)
  0.4% Garden Cosmos (Cosmos bipinnatus)
  0.4% Farewell-To-Spring (Clarkia amoena)
  0.4% Dwarf Fireweed (Chamaenerion latifolium)
```

## Dependencies

Several things need to be installed in order for `nature-id.py` to run. Some Python packages are required, classification models need to be downloaded and installed into the `classifiers` directory, and finally the taxonomy and common names need to be downloaded into the `inaturalist-taxonomy` directory.

### Python Packages

This code is written in Python 3. Besides Python 3, the packages `Pillow` and `requests` are used to load and process images and to access the iNaturalist API.

These packages as well as `TensorFlow Lite` can be installed on Ubuntu Linux and other Debian distributions with the command

```
sudo apt install python3-pillow python3-requests
pip3 install tflite-runtime
```

and on other platforms with the command

```
pip install Pillow requests tflite-runtime
```

Where appropriate `pip3` should be called instead of `pip` to avoid accidentally installing Python 2 packages.


### Classification Models

**The following instructions appear not to work anymore since the models moved from google.com to kaggle.com. [Issue #1](https://github.com/joergmlpts/nature-id/issues/1) tracks this issue.**

The classification models and their labelmap files have to be downloaded from Google and they go into directory `classifiers`.

The classifiers can be downloaded from these links:

 * [classifier for plants](https://tfhub.dev/google/aiy/vision/classifier/plants_V1/1)
 * [classifier for birds](https://tfhub.dev/google/aiy/vision/classifier/birds_V1/1)
 * [classifier for insects](https://tfhub.dev/google/aiy/vision/classifier/insects_V1/1)

Each classifier consists of a `.tflite` model and a `.csv` labelmap file. Both are required.

On the web pages above scroll down and under **Output** click on *labelmap* to download and save the labels. On Windows, the default action for a .csv file might be to open it in Excel. Be certain to save the .csv file to disk instead. Then scroll back up and under **Model formats** switch to *TFLite (aiyvision/classifier/...)*. There click on *Download* to get the `.tflite` file. Please also note the paragraphs at the bottom of these web pages about appropriate and inappropriate use cases and licensing.

### Taxonomy and Common Names Files

The trained models come with scientific names as labels and many of these scientific names are already outdated. The common names and the current taxonomy are obtained from this file: [https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip](https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip) This tool expects this zip archive in the `inaturalist-taxonomy` directory.

## Example Images

Example Images pictures of plants are provided in the `plant_images` directory. The filenames indicate the species that I think is in the photo. Note that these examples only lead to successful identification to varying degrees. The *Mentzelia lindleyi* is certainly not correctly identified.

## Messages

The first call with a model transforms the labels into a taxonomic hierarchy. Each label is replaced with its representation in the current taxonomy and all its ancestors are added. This process takes some time and results in many messages. Once the hierarchy has been successfully computed, it is written to disk. Future calls to `nature_id.py` will load the taxonomic hierarchy from disk instead of reading the labels and computing the taxonomy again.

This is what the first calls look like. Again, we use the plant model as an example. The bird and insect models are smaller and result in fewer messages.

```
PS C:\nature-id> python -m plants nature_id.py .\plant_images
Read 2,102 labels from 'classifiers\aiy_plants_V1_labelmap.csv' in 0.0 secs.
Loading iNaturalist taxonomy...
Loaded iNaturalist taxonomy of 993,552 taxa in 15.2 secs.
Info: Taxon for label 'background' not found, inserting as pseudo-kingdom.
Info: Taxon 'Eichhornia crassipes' changed to 'Pontederia crassipes', iNat taxa id 962637.
Info: Taxon 'Potentilla anserina' changed to 'Argentina anserina', iNat taxa id 158615.
Info: Taxon 'Stenosiphon linifolius' changed to 'Oenothera glaucifolia', iNat taxa id 914092.
Info: Taxon 'Sophora secundiflora' changed to 'Dermatophyllum secundiflorum', iNat taxa id 499559.
Info: Taxon 'Mimulus bigelovii' changed to 'Diplacus bigelovii', iNat taxa id 701989.
Info: Taxon 'Botrychium dissectum' changed to 'Sceptridium dissectum', iNat taxa id 122085.
Info: Taxon 'Trientalis borealis' changed to 'Lysimachia borealis', iNat taxa id 204174.
Info: Taxon 'Hyptis emoryi' changed to 'Condea emoryi', iNat taxa id 489286.
Info: Taxon 'Opuntia engelmannii lindheimeri' changed to 'Opuntia lindheimeri', iNat taxa id 119980.
Info: Taxon 'Aquilegia caerulea' changed to 'Aquilegia coerulea', iNat taxa id 501742.
Info: Taxon 'Fuscospora cliffortioides' changed to 'Nothofagus cliffortioides', iNat taxa id 404204.
Info: Taxon 'Cooperia drummondii' changed to 'Zephyranthes chlorosolen', iNat taxa id 554401.
Info: Taxon 'Dracopis amplexicaulis' changed to 'Rudbeckia amplexicaulis', iNat taxa id 200073.
Info: Taxon 'Dodecatheon meadia' changed to 'Primula meadia', iNat taxa id 549981.
Info: Taxon 'Aptenia cordifolia' changed to 'Mesembryanthemum cordifolium', iNat taxa id 589815.
Info: Taxon 'Chamerion latifolium' changed to 'Chamaenerion latifolium', iNat taxa id 564970.
Info: Taxon 'Echinocereus mojavensis' changed to 'Echinocereus triglochidiatus mojavensis', iNat taxa id 858352.
Warning: multiple taxa named 'Aquilegia vulgaris': species 51807, complex 1042772; choosing species.
Info: Taxon 'Dodecatheon pulchellum' changed to 'Primula pauciflora', iNat taxa id 498086.
Info: Taxon 'Mimulus lewisii' changed to 'Erythranthe lewisii', iNat taxa id 777190.
Info: Taxon 'Sambucus nigra canadensis' changed to 'Sambucus canadensis', iNat taxa id 84300.
Info: Taxon 'Asyneuma prenanthoides' changed to 'Campanula prenanthoides', iNat taxa id 851072.
Info: Taxon 'Anemone quinquefolia' changed to 'Anemonoides quinquefolia', iNat taxa id 950598.
Info: Taxon 'Hedypnois cretica' changed to 'Hedypnois rhagadioloides', iNat taxa id 492864.
Warning: multiple taxa named 'Achillea millefolium': species 52821, complex 1105043; choosing species.
Info: Taxon 'Anagallis arvensis' changed to 'Lysimachia arvensis', iNat taxa id 791928.
Info: Taxon 'Hieracium caespitosum' changed to 'Pilosella caespitosa', iNat taxa id 711086.
Info: Taxon 'Potentilla anserina pacifica' changed to 'Argentina pacifica', iNat taxa id 524900.
Info: Taxon 'Sambucus nigra caerulea' changed to 'Sambucus cerulea', iNat taxa id 143799.
Info: Taxon 'Polygala californica' changed to 'Rhinotropis californica', iNat taxa id 876453.
Info: Taxon 'Calylophus berlandieri' changed to 'Oenothera berlandieri', iNat taxa id 359779.
Info: Taxon 'Mimulus cardinalis' changed to 'Erythranthe cardinalis', iNat taxa id 319974.
Info: Taxon 'Callistemon citrinus' changed to 'Melaleuca citrina', iNat taxa id 77976.
Info: Taxon 'Liatris mucronata' changed to 'Liatris punctata mucronata', iNat taxa id 371814.
Warning: multiple taxa named 'Stellaria media': species 53298, complex 1087592; choosing species.
Info: Taxon 'Anemone americana' changed to 'Hepatica americana', iNat taxa id 741014.
Info: Taxon 'Anemone occidentalis' changed to 'Pulsatilla occidentalis', iNat taxa id 60482.
Info: Taxon 'Orobanche fasciculata' changed to 'Aphyllon fasciculatum', iNat taxa id 802543.
Info: Taxon 'Mimulus primuloides' changed to 'Erythranthe primuloides', iNat taxa id 635401.
Info: Taxon 'Polygala paucifolia' changed to 'Polygaloides paucifolia', iNat taxa id 497911.
Warning: multiple taxa named 'Campanula rotundifolia': species 62312, complex 984576; choosing species.
Info: Taxon 'Cissus incisa' changed to 'Cissus trifoliata', iNat taxa id 133333.
Info: Taxon 'Schinus terebinthifolius' changed to 'Schinus terebinthifolia', iNat taxa id 130872.
Info: Taxon 'Cooperia pedunculata' changed to 'Zephyranthes drummondii', iNat taxa id 120026.
Info: Taxon 'Scabiosa atropurpurea' changed to 'Sixalix atropurpurea', iNat taxa id 372376.
Info: Taxon 'Sphenosciadium capitellatum' changed to 'Angelica capitellata', iNat taxa id 704166.
Info: Taxon 'Trientalis latifolia' changed to 'Lysimachia latifolia', iNat taxa id 496537.
Warning: multiple taxa named 'Spiranthes cernua': species 773385, complex 931407; choosing species.
Info: Taxon 'Spartina pectinata' changed to 'Sporobolus michauxianus', iNat taxa id 772984.
Info: Taxon 'Centaurea americana' changed to 'Plectocephalus americanus', iNat taxa id 699778.
Info: Taxon 'Fuscospora solandri' changed to 'Nothofagus solandri', iNat taxa id 70246.
Info: Taxon 'Heliotropium tenellum' changed to 'Euploca tenella', iNat taxa id 769888.
Info: Taxon 'Blechnum spicant' changed to 'Struthiopteris spicant', iNat taxa id 774894.
Info: Taxon 'Fallopia japonica' changed to 'Reynoutria japonica', iNat taxa id 914922.
Info: Taxon 'Echinocactus texensis' changed to 'Homalocephala texensis', iNat taxa id 870496.
Info: Taxon 'Gaura parviflora' changed to 'Oenothera curtiflora', iNat taxa id 78241.
Info: Taxon 'Parentucellia viscosa' changed to 'Bellardia viscosa', iNat taxa id 537967.
Info: Taxon 'Anemone nemorosa' changed to 'Anemonoides nemorosa', iNat taxa id 950603.
Info: Taxon 'Hieracium aurantiacum' changed to 'Pilosella aurantiaca', iNat taxa id 711103.
Info: Taxon 'Anemone hepatica' changed to 'Hepatica nobilis', iNat taxa id 639660.
Info: Taxon 'Merremia dissecta' changed to 'Distimake dissectus', iNat taxa id 907480.
Info: Taxon 'Anemone canadensis' changed to 'Anemonastrum canadense', iNat taxa id 881527.
Info: Taxon 'Chamerion angustifolium' changed to 'Chamaenerion angustifolium', iNat taxa id 564969.
Info: Taxon 'Lychnis flos-cuculi' changed to 'Silene flos-cuculi', iNat taxa id 740984.
Throttling API calls, sleeping for 44.5 seconds.
Info: Taxon 'Ampelopsis brevipedunculata' changed to 'Ampelopsis glandulosa brevipedunculata', iNat taxa id 457553.
Info: Taxon 'Anemone acutiloba' changed to 'Hepatica acutiloba', iNat taxa id 179786.
Info: Taxon 'Pennisetum setaceum' changed to 'Cenchrus setaceus', iNat taxa id 430581.
Info: Taxon 'Mimulus guttatus' changed to 'Erythranthe guttata', iNat taxa id 470643.
Info: Taxon 'Blechnum fluviatile' changed to 'Cranfillia fluviatilis', iNat taxa id 700995.
Info: Taxon 'Blechnum discolor' changed to 'Lomaria discolor', iNat taxa id 403546.
Info: Taxon 'Andropogon gerardii' changed to 'Andropogon gerardi', iNat taxa id 121968.
Info: Taxon 'Ferocactus hamatacanthus' changed to 'Hamatocactus hamatacanthus', iNat taxa id 855937.
Info: Taxon 'Gaura lindheimeri' changed to 'Oenothera lindheimeri', iNat taxa id 590726.
Info: Taxon 'Gaura suffulta' changed to 'Oenothera suffulta', iNat taxa id 521639.
Info: Taxon 'Glottidium vesicarium' changed to 'Sesbania vesicaria', iNat taxa id 890511.
Info: Taxon 'Acacia farnesiana' changed to 'Vachellia farnesiana', iNat taxa id 79472.
Warning: multiple taxa named 'Rubus fruticosus': complex 55911, species 1090496; choosing species.
Info: Taxon 'Othocallis siberica' changed to 'Scilla siberica', iNat taxa id 862704.
Info: Taxon 'Mimulus aurantiacus' changed to 'Diplacus', iNat taxa id 777236.
Info: Taxon 'Phoradendron tomentosum' changed to 'Phoradendron leucarpum', iNat taxa id 49668.
Info: Taxon 'Orobanche uniflora' changed to 'Aphyllon uniflorum', iNat taxa id 802714.
Info: Taxon 'Rosmarinus officinalis' changed to 'Salvia rosmarinus', iNat taxa id 636795.
Info: Taxon 'Cynoglossum grande' changed to 'Adelinia grande', iNat taxa id 769151.
Computed taxonomic tree from labels in 64.8 secs: 4,091 taxa including 2,102 leaf taxa.
Taxonomy written to file 'classifiers\aiy_plants_V1_taxonomy.csv'.
Reading common names from 'inaturalist-taxonomy\inaturalist-taxonomy.dwca.zip' member 'VernacularNames-english.csv'...
Read 203,093 common names in 1.5 secs, loaded 3,071 in language "en_US" for 4,091 taxa.
```

### Messages Explained

```
Read 2,102 labels from 'classifiers\aiy_plants_V1_labelmap.csv' in 0.0 secs.
```

`nature-id` reads a label file. If no errors occur, a taxonomy will be written for these labels and further runs will load `classifiers\aiy_plants_V1_taxonomy.csv` instead.

```
Loading iNaturalist taxonomy...
Loaded iNaturalist taxonomy of 993,552 taxa in 15.2 secs.
```

The entire iNaturalist taxonomy of about 1 million taxa is loaded. `nature-id` will look up the labels in this taxonomy and insert them, along with all their ancestors, into a taxonomy for the labels.

```
Info: Taxon for label 'background' not found, inserting as pseudo-kingdom.
```

Label `background` was not found. It is not a species, but denotes something else in the Google model. It is treated as a kingdom in the taxonomy; it has no ancestors.

```
Info: Taxon 'Potentilla anserina' changed to 'Argentina anserina', iNat taxa id 158615.
```

In the current taxonomy, this species belongs to a different genus. The numeric ID in this message is useful for getting more information. This number can be prefixed with `https://www.inaturalist.org/taxa/` and opened in a browser: [https://www.inaturalist.org/taxa/158615](https://www.inaturalist.org/taxa/158615).

```
Warning: multiple taxa named 'Achillea millefolium': species 52821, complex 1105043; choosing species.
```

The label name for this common yarrow is not unique, there are several taxa for this scientific name.  `nature-id` assumes that the species is the one we want.

```
Throttling API calls, sleeping for 44.5 seconds.
```

This message is followed by 45 seconds of silence. When a name is not found in the the current taxonomy, the one previously loaded with about 1 million taxa, then iNaturalist API calls are made to look up the inactive scientific name. The iNaturalist team would like us to throttle API calls to no more than 60 calls per minute. This delay has been implemented to accommodate their request.

```
Info: Taxon 'Mimulus aurantiacus' changed to 'Diplacus', iNat taxa id 777236.
```

The species *Mimulus aurantiacus* in the label file is replaced with the genus *Diplacus* and not with the current species *Diplacus aurantiacus*. This looks like a bug and hence deserves a closer look.

The reason for this decision of `nature_id` is that *Mimulus aurantiacus* consisted of several varieties *Mimulus aurantiacus aurantiacus*, *Mimulus aurantiacus grandiflorus*, *Mimulus aurantiacus parviflorus*, and 3 more.

In the current taxonomy, these varieties are species *Diplacus aurantiacus*, *Diplacus grandiflorus*, and *Diplacus parviflorus*. *Diplacus aurantiacus* does not replace *Mimulus aurantiacus*; it replaces the variety *Mimulus aurantiacus aurantiacus*.

Another way to understand this issue is to realize that photos of all varieties *Mimulus aurantiacus aurantiacus*, *Mimulus aurantiacus grandiflorus*, *Mimulus aurantiacus parviflorus* and the 3 others were used to train the classification model to recognize *Mimulus aurantiacus*. In the current taxonomy, this label is triggered for each of the species *Diplacus  aurantiacus*, *Diplacus grandiflorus*, and *Diplacus parviflorus*. `nature_id` cannot say which of current species it sees. It can only identify images as genus *Diplacus*.

```
Taxonomy written to file 'classifiers\aiy_plants_V1_taxonomy.csv'.
```

A taxonomy for the scientific names in the label file has been successfully computed and this taxonomy was written to disk. Future calls will load this taxonomy instead of loading the labels and re-computing the taxonomy.

```
Reading common names from 'inaturalist-taxonomy\inaturalist-taxonomy.dwca.zip' member 'VernacularNames-english.csv'...
Read 203,093 common names in 1.5 secs, loaded 3,071 in language "en_US" for 4,091 taxa.
```

Common names have been read. The common names are always selected for the local language, not necessarily for English as shown here.
