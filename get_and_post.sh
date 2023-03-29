#!/bin/bash

# Run the Python script
PATH=$PATH:/home/pmin/.cache/selenium/chromedriver/linux64/111.0.5563.64/
/home/pmin/miniconda3/bin/conda run -n gpt python get_toots.py
/home/pmin/miniconda3/bin/conda run -n gpt python post_toots.py