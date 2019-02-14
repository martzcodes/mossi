# MOSS-improved

## Step 0: Install requirements

My computer was all over the place when I wrote these... so I don't have a specific requirements.txt ... but here's what to install:

`pip install mosspy`

`pip install beautifulsoup4`

`pip install pdfkit`

Install https://wkhtmltopdf.org/

## Step 1: Prep

I used `<assignment>-<semester>-<year>`. Use the same convention for previous semesters work if you're comparing to those. Naming convention is only really for convenience but is used later to determine if a student is "current" or not. If your assignment has multiple files to compare, put those in a sub folder for each.

Next, update `mossi.py` with your MOSS user id and the other stuff in the config section

## Step 2: Run MOSSI

`python mossi.py`

It may take a while to upload the files.

At the end you'll get a few json files output.

## Step 3: Identify students and gather evidence

Update `evidence.json` and add studentnames (as they're formatted in the files, how they were output in the jsons) to process for evidence.

Update the OUTPUT_FOLDER in `evidence.py` if you want.

Run `python evidence.py`
