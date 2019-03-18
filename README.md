# MOSS-improved

## Step 0: Install requirements

My computer was all over the place when I wrote these... so I don't have a specific requirements.txt ... but here's what to install:

`pip install mosspy`

`pip install beautifulsoup4`

`pip install pdfkit`

`pip install networkx`

Install https://wkhtmltopdf.org/

## Step 1: Prep

`python bonnie.py assignment_2 ai/a2-anon ai/a2 spring-2019`

Where assignment_2 is from the bonnie downloaded results for the submission zip file (e.g. studentname-assignment_2-datetimestamp)

`ai/a2-anon` is where the bonnie code has been unzipped to

`ai/a2` is the output folder... this will be the correct folder structure to be used in the mossi step.

and `spring-2019` is the current semester (or the semester that you're using)

Next, update `mossi.py` with your MOSS user id and the other stuff in the config section

## Step 2: Add previous semester stuff

From Step 1 above you should have an `ai/a2` output... it will have a folder within it for each file submitted.  You can add previous semester / watermarked files in subfolders and they'll be included... e.g. `ai/a2/search_submission/watermarked/<files>`

## Step 3: Run MOSSI

`python mossi.py ai/a2 ai/a2-out spring-2019`

Where `ai/a2` is the location of your files, including previous semesters / watermarks (from above)

`ai/a2-out` is where MOSS results are locally stored and output files are placed.

`spring-2019` is the current semester... it should match what you used before

It may take a while to upload the files.

At the end you'll get a few json files output in the output directory.

## Step 4: Identify students and gather evidence

Update `evidence.json` and add studentnames (as they're formatted in the files, how they were output in the jsons) to process for evidence.

Update the OUTPUT_FOLDER in `evidence.py` if you want.

Run `python evidence.py`
