#!/bin/sh
rm -f inaturalist-taxonomy.dwca.zip
curl https://www.inaturalist.org/taxa/inaturalist-taxonomy.dwca.zip \
     -o inaturalist-taxonomy.dwca.zip
