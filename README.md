Neuroimaging hub - UPF
=======================
## Description
The idea behind this repository is to serve as a hub for all the processing, registration and
distribution of neuroimaging files. This repository is composed of:
* Scripts to apply different procedures to neuroimages, such as registration, preprocessing or segmentation.
* A wiki, where procedures and tutorials for the scripts and other aspects are commented.
* An issue system, where questions about the code can be directly asked.


The repository structure allow us to update both the code and the wiki simultaneously
and to quickly fix any issues or questions we may have, as well as having a single pipeline
and centralizing all our code. Remember to not upload anything
## Table of contents
The file structure of the code is subject to change:
* **scripts** - Python scripts to process images. There are several subfolders there:
  * **libs**: General libraries that all scripts use.
  * **PET-pipeline:** Scripts to extract features from a PET image using an atlas.
  * **quick_scripts:** Folder with small scripts to do concrete things.
  * **spm-pipeline:** Scripts to use in SPM (https://www.fil.ion.ucl.ac.uk/spm/software/spm12/)
* **hpc_scripts** - Used to launch scripts from the other folder in the HPC cluster. Each script are shown as examples, and should be modified to the user's need.

### Project wiki
The wiki is hosted in this same repository. The idea is the wiki to host
detailed pipelines, guides and explanations about the procedures to follow. For example:
* A page on useful tools and software for visualization.
* A page detailing learning resources for registration.
* A page describing the processing pipeline of a T1 MRI image.
* And many more!
The idea is this repository to serve as support for work done in this project and
subsequent projects, and that we can have a hub of information for any other
students or researchers.

To access the wiki, click on the link above or, alternatively, [**here**](https://github.com/GerardMJuan/upf-neuroimage-preprocess-hub/wiki).

## Usage and Contributing
The idea is to update the scripts and the wiki together! As you do your work, the
scripts you use can be put here, and the procedures/difficulties/new ideas you find can
be put in the issues section or in a new page in the wiki.

For now, this repository is private. May put it public after some months of work.

## Credits
* Gerard Martí - gerard.marti@upf.edu. Wiki and comments, and some of the scripts.
* Gerard Sanroma - gerard.sanroma@upf.edu. Scripts.

## License
MIT License. Details in the LICENSE file.
