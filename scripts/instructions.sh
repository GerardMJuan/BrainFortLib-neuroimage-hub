
To follow this pipeline we need a folder called pipeline. Inside this folder we need to have the following files and 3 sub-folders (brain_extraction, PET_original and atlas:

FILES:

    icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii
    register_to_template.py
    register_to_baseline.py
    register_to_pet.py
    register_to_atlas.py
    register_to_label.py
    scheduler.py
    
FOLDERS:

    brain_extraction: containing all the extracted brains to work with
    PET_original: containing all the PET raw images
    atlas: containing the BCI-DNI MRI image and the labels image
      BCI-DNI MRI image.nii.gz
      BCI-DNI_brain.label.nii.gz
    
  




####     1. Registration of the MRI brain extracted: SyN register, template = mask

python register_to_template.py --in_dir /homedtic/pjavierre/pipeline/brain_extraction --img_suffix .nii.gz --template_file /homedtic/pjavierre/pipeline/icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii --out_dir /homedtic/pjavierre/pipeline/brain_extraction_registered  --out_warp_intfix test --transform Syn 1 --output_warped_image 


####     2. Alignment of the PET-MRI images: Registration of the original PET image to the MRI brain extracted image

python register_to_baseline.py --in_dir /homedtic/pjavierre/pipeline/PET_original --img_suffix _pet.nii.gz --template_dir /homedtic/pjavierre/pipeline/brain_extraction --out_dir /homedtic/pjavierre/pipeline/PET_MRI  --out_warp_intfix test --transform Rigid 1 --output_warped_image




####     3. Registration of the PET images: Using ApplyTransforms


python register_to_pet.py --in_dir /homedtic/pjavierre/pipeline/PET_MRI --img_suffix .nii.gz  --matrix_dir /homedtic/pjavierre/pipeline/brain_extraction_registered/ --out_dir /homedtic/pjavierre/pipeline/PET_registered --out_warp_intfix test --interpolation Linear --mask /homedtic/pjavierre/pipeline/icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii --output_warped_image




####     4. Registration of the BCI-DNI MRI image (moving) to the PET/MRI image registered (and aligned) (fixed): rigid 1, interpolation lineal
# it is just a version of register _to_template.py, where template and moving image positions have been switched

python register_to_atlas.py --in_dir /homedtic/pjavierre/pipeline/PET_registered --img_suffix .nii.gz --template_file /homedtic/pjavierre/pipeline/atlas/BCI-DNI_brain.label.nii.gz --out_dir /homedtic/pjavierre/pipeline/atlas_registered  --out_warp_intfix test --transform Rigid 1  --output_warped_image



####     5. Alignment of the BCI-DNI Atlas Labels to the PET/MRI: ApplyTransforms, interpolation GenericLabel
# it is just a version of register_to_pet.py, where image and matrix positions have been switched

python register_to_label.py --in_dir /homedtic/pjavierre/pipeline/atlas_registered/ --mat_suffix .mat  --label_dir /homedtic/pjavierre/pipeline/atlas/BCI-DNI_brain.label.nii.gz --out_dir /homedtic/pjavierre/pipeline/labels/ --out_warp_intfix test --interpolation GenericLabel --mask /homedtic/pjavierre/pipeline/icbm_avg_152_t1_tal_nlin_symmetric_VI_mask.nii --output_warped_image


####	 6. Extraction of masks, ROIs and mean pixel value
python pipeline.py
