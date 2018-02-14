# ADNI Metadata Extraction instructions

This file will detail how to extract the metadata from the ADNI Database and store it in a .csv file for posterior use. We will detail each script, what it does, and how it works.

## Getting Started

These instructions will help replicating the metadata extraction to obtain a .csv file with the following characteristics:

    S_ID        1		# Subject ID
    IM_ID       2		# Image ID (Study ID)
    GENDER      3		# Gender of the subject
    AGE         4		# Age of the subject at time of scan
    WEIGHT      5		# Weight of the subject at time of scan
    GROUP       6		# Group of the subject
    APOE_A1     7		# APOE_A1 genotype value of the subject
    APOE_A2     8		# APOE_A2 genotype value of the subject
    MMSE        9		# MMSE score of the subject at the time of scan
    CDR         10		# CDR value of the subject at the time of scan
    DATE        11		# Date of scan
    GROUP_ID    12		# Group_id / Class (CN,MCI,AD) of the baseline
    IMAGE_PATH  13		# Path where the original image is stored
    DX_FOLLOWUP 14		# Group_id/ Class of the sample
    CHANGE      15		# -1 if there is change, else, type of change
    TTC         16		# Time to convert (to the change) 

In each script file we will go more on detail in how to obtain each column

### Prerequisites

The prerrequisites are:

* Download the ADNI database from its website (http://adni.loni.usc.edu/)
* Make sure that there is a .xml file for each sample and that the directory structure is conserved.
* Download the file ADNIMERGE.csv from the website (http://adni.loni.usc.edu/)
* Create an ADNIMERGE_reduced.csv with only the following columns: RID	PTID	EXAMDATE	DX_bl	DX	Month_bl	Month
* (Optional) (TODO: Make this REALLY optional): Extract data from (https://sites.google.com/site/machinelearning4mcitoad/) for extended MCI labels

### Scripts for creating the metadata

The scripts relevant to the metadata extraction are:

* create_metadata.py: Script that creates the base metadata from the ADNI database, but without including conversion and followup details.
* modify_metadata_followups.py: Script that combines the ADNIMERGE_reduced.csv information about the conversion and followup diagnostics and the metadata extracted previously and combines it 
* cfg_md.py: small file with configuration parameters such as where the directories are, name of the output files, and so on.

### Execution instructions

1. First, modify the cfg_md.py file to configure the scripts: the directories where the .csv files and the ADNI database are, as well as the name and location of the different output files.
2. Then, execute create_metadata.py

```
python3 create_metadata.py
```

This will create a intermediate metadata file in the given location.

3. Execute modify_metadata_followups.py


```
python3 modify_metadata_followups.py
```

This will create the final metadata file.


## Author

* **Gerard Martí** - (gerard.marti@upf.edu)


## License

No license right now, this is for myself lmao


## Acknowledgments

* Sergi Roberto, for scoring that goal
