# Download Instructions

The [Tensorflow Lite](https://www.tensorflow.org/lite/guide) classifiers that go in this directory can be downloaded from these websites:

 * [classifier for plants](https://tfhub.dev/google/aiy/vision/classifier/plants_V1/1)
 * [classifier for birds](https://tfhub.dev/google/aiy/vision/classifier/birds_V1/1)
 * [classifier for insects](https://tfhub.dev/google/aiy/vision/classifier/insects_V1/1)

Each classifier consists of a `.tflite` model and a `.csv` labelmap file. Both are required.

On each of the above websites scroll down and under `Output` click on `labelmap` to download the labels. Then scroll back up and under `Model formats` switch to `TFLite (aiyvision/classifier/...)`. There click on `Download` to get the `.tflite` file.

If you happen to have the classifier included in [Seek](https://www.inaturalist.org/pages/seek_app), it can go in this directory as well. It consists of two files `optimized_model_v1.tflite` and `taxonomy_v1.csv`.
