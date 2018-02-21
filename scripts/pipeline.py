
# coding: utf-8

# In[1]:


### %matplotlib inline 
import numpy as np
import nibabel as nib
import os
import fnmatch

os.chdir("/home/Paula/pipeline/labels") #cogemos este directorio random, no importa porque los archivos tienen el mismo prefijo
os.listdir(".")
r=[]
for x in os.listdir('.'):
    r.append(x[:16],) #Para que solo coja el prefijo de cada imagen

    if len(r) > 10: #Para que no coja el archivo temporal del notebook. En este caso es 10 porque tenemos 10 pacientes
        r = r[1:16]
print r
    

# Creamos directorio de salida donde guardar las ROI
directory='/home/Paula/pipeline/ROI'
if not os.path.exists(directory):
    os.makedirs(directory)


v = 0
for v in r:
    
    label = nib.load('/home/Paula/pipeline/labels/{}_ses-M00_task-rest_acq-fdg_pettestWarpedPETWarpedtest0GenericAffineLabelWarped.nii.gz'.format(v)) #Labels del atlas registrados a nuestro espacio
    pet = nib.load('/home/Paula/pipeline/PET_registered/{}_ses-M00_task-rest_acq-fdg_pettestWarpedPETWarped.nii.gz'.format(v)) #PET al que queremos sacar ROIs
    mri = nib.load('/home/Paula/pipeline/brain_extraction_registered/{}_ses-M00_T1w_Rigid_Warped_braintestWarped.nii.gz'.format(v)) #MRI al que queremos sacar ROIs

    
    affine_label = label.affine #Cogemos esta matriz porque todos los tipos de imagenes tienen la misma

    # Pasamos las Nifti images a arrays
    label = np.around(np.array(label.dataobj))


    # Sacamos los valores unicos (labels)
    unique_label, index_label, counts_label= np.unique(label, return_index=True, return_counts=True)
    unique_label=unique_label.astype(int) #para que no de problemas al hacer counts[t]
    
    print 'Loading images of pacient {}  ...'.format(v)
    
    os.chdir("/home/Paula/pipeline") #cogemos este directorio random, no importa porque los archivos tienen el mismo prefijo
        
    np.savetxt('Labels.txt', unique_label)
    
    os.chdir("/home/Paula/pipeline/labels")

    i=0
    mean_pet = []
    mean_mri = []

    for i in unique_label: 

    #Inicializamos para cada iteracion

        mask = np.zeros((label.shape[0],label.shape[1],label.shape[2],label.shape[3]))
        pet2 = np.array(pet.dataobj) # No hay que poner around, ya estan normalizadas
        mri2 = np.array(mri.dataobj) # No hay que poner around, ya estan normalizadas


        mask[label == i] = 1 
        pet2[mask==0]=0
        mask2=mask.reshape(193,229,193) #Porque la imagen MRI es 3D y no 4D como las demas
        mri2[mask2==0]=0

    #Calculamos numero total de pixeles de cada mask

        pixels = sum(sum(sum(sum(mask))))

    #Sumamos los valores de las imagenes y dividimos entre el numero de pixeles de la mask para sacar el valor medio del label

        roi_pet = sum(sum(sum(sum(pet2))))
        t = roi_pet / pixels
        mean_pet.append(t,)
        #print 'PET of pacient {}, label {} has {} mean pixel value'.format(v,i,t)
        
    #Guardamos el array que contiene todos los valores medios de cada ROI
    
    
        os.chdir("/home/Paula/pipeline") #cogemos este directorio random, no importa porque los archivos tienen el mismo prefijo
        
        np.savetxt('mean_pet_{}_.txt'.format(v), mean_pet)
        
        
        
        
        
        #SUVtarget = t
        #SUVref = 
        #SUVR = SUVtarget/SUVref

        roi_mri = sum(sum(sum(mri2)))
        w = roi_mri / pixels
        mean_mri.append(w,)
        #print 'MRI of pacient {}, label {} has {} mean pixel value'.format(v,i,w)


    #Pasamos los array a Nifti images

        #datas_mask = mask.reshape(label.shape[0],label.shape[1],label.shape[2],label.shape[3])
        #new_image_mask = nib.Nifti1Image(datas_mask, affine_label)

        #datas_pet = pet2.reshape(label.shape[0],label.shape[1],label.shape[2],label.shape[3])
        #new_image_pet = nib.Nifti1Image(datas_pet, affine_label)

        #datas_mri = mri2.reshape(label.shape[0],label.shape[1],label.shape[2],label.shape[3])
        #new_image_mri = nib.Nifti1Image(datas_mri, affine_label)


    #Para guardar las imagenes

        #nib.save(new_image_mask,'/home/Paula/pipeline/ROI/Mask_{}_Label{}.nii.gz'.format(v,i))
        #nib.save(new_image_pet,'/home/Paula/pipeline/ROI/PET_{}_Label{}.nii.gz'.format(v,i))
        #nib.save(new_image_mri,'/home/Paula/pipeline/ROI/MRI_{}_Label{}.nii.gz'.format(v,i))

        i = i+1
    
    
    print 'The PET mean pixel value from pacient {} is {}'.format(v,mean_pet)
    print 'The MRI mean pixel value from pacient {} is {}'.format(v,mean_mri)
    
    

    #print 'The generated Nifti images have {} dimension'.format(new_image_mask.shape)
    #print 'Registered label atlas image has {} labels'.format(max(unique_label.shape))


# Volvemos al directorio principal que es donde hemos guardado todo
os.chdir("/home/Paula/pipeline")


#Calcular SUVR para cada paciente
#Cargamos el diccionario para ver la correspondencia entre posicion del array con el label 
t = np.loadtxt('Labels.txt')
j = np.arange(0,97,1)


dictionary = dict(zip(j,t))
print 'The correspondence between array position and label is the following:\n{}'.format(dictionary)

#Escoger que label queremos. Por ejemplo, queremos como referencia el label 900 que es el cerebelo. 
#Entonces sera la posicion 95 de nuestro array de mean values

filelist = [ f for f in os.listdir("/home/Paula/pipeline") if f.endswith("_.txt") ]
selected_label = 95
for f in filelist:
    SUVtarget = np.loadtxt(f)
    SUVref = SUVtarget[selected_label]
    SUVR = SUVtarget/SUVref
    print 'The SUVR of pacient {} for label {} is:\n {}'.format(f[13:25],selected_label,SUVR)
    
        

