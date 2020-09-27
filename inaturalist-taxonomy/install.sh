#!/bin/sh
rm -f *.csv *.xml *.zip
curl https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip \
     -o inaturalist-taxonomy.dwca.zip
unzip inaturalist-taxonomy.dwca.zip
rm inaturalist-taxonomy.dwca.zip
