"""
Plot the simliarities of a dataset.

Given a file with the similarities of a dataset, plot it
in a two-dimensional embedding.
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'gsanroma'

import argparse
import numpy as np
import os
from sklearn.manifold import SpectralEmbedding
from sklearn import cluster
from pickle import load
from scipy.spatial import distance
from xml.etree import ElementTree
from xml.etree.ElementTree import Element
from xml.etree.ElementTree import SubElement
import matplotlib

# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')

import matplotlib.pyplot as plt

# # Decides images at each fold by maximizing the spread among the selected images in the manifold

parser = argparse.ArgumentParser()
parser.add_argument("--scores_file", type=str, nargs=1, required=True)
parser.add_argument("--num_atlas", type=int, nargs=1, required=True)
parser.add_argument("--metadata_file")
parser.add_argument("--out_fig", type=str, nargs=1)
parser.add_argument("--out_val_xml", type=str, nargs=1, help='out_file_xml')
parser.add_argument("--out_tst_xml", type=str, nargs=1, help='out_file_xml')
parser.add_argument("--create_symlinks", type=str, nargs=5, help='symlink_dir_prefix, base_dir, img_suffix, label_suffix, scores_img_suffix')

args = parser.parse_args()

f = open(args.scores_file[0], 'rb')
#s = f.read()
in_dir, in_files_list, in2_dir, in2_files_list, scores = load(f)
print(in_dir)
print(in2_dir)
print(in_files_list)
f.close()

assert in_dir == in2_dir and in_files_list == in2_files_list, "Not same files"

Natlas = args.num_atlas[0]

plt.matshow(scores,vmin=0.65, vmax=1.0, cmap='hot')
plt.colorbar()
plt.savefig('scores.png')

Y = SpectralEmbedding(n_components=2, affinity='precomputed').fit_transform(scores)

labels = cluster.KMeans(Natlas).fit_predict(Y)

N = Y.shape[0]

# Computation of cluster representatives
centers = np.zeros((Natlas, Y.shape[1]))
for i in range(Natlas):
    centers[i] = np.mean(Y[labels == i], axis=0)

D = distance.cdist(centers, Y, metric='euclidean', p=2)

atlas_idx = list(np.argmin(D, axis=1))
target_idx = list(set(range(N)) - set(atlas_idx))


if args.out_fig is not None:
    distinct_colors = plt.get_cmap('jet')(np.linspace(0, 1.0, Natlas))

    colors = np.zeros((N, 4))
    for i in range(N):
        colors[i] = distinct_colors[labels[i]]

    plt.figure("Number of clusters: {}".format(Natlas))
    plt.scatter(Y[:, 0], Y[:, 1], c=colors, cmap=plt.cm.Spectral)

    for i in range(N):
        plt.annotate('{}'.format(i), (Y[i, 0], Y[i, 1]), fontsize=7)
    plt.scatter(centers[:,0], centers[:,1], marker='x')
    plt.scatter(Y[atlas_idx, 0], Y[atlas_idx, 1], s=80, facecolors='none', edgecolors='r')
    plt.savefig(args.out_fig[0])


if args.out_val_xml is not None:

    folds_xml = Element('folds')
    # SubElement(folds_xml, 'template_file', value=os.path.join(base_dir, 'processed', 'template.nii.gz'))

    for i_fold in atlas_idx:

        # Train
        fold_xml = SubElement(folds_xml, 'fold')
        train_xml = SubElement(fold_xml, 'train')
        SubElement(train_xml, 'base_dir', value=in_dir)

        for i in set(atlas_idx) - {i_fold}:
            # name = in_files_list[i].split(args.out_val_xml[1])[0].split(args.out_val_xml[2])[0]
            SubElement(train_xml, 'subject', image=in_files_list[i])#name + args.out_val_xml[1], labelmap=name + args.out_val_xml[2])

        # Test fold
        test_xml = SubElement(fold_xml, 'test')
        SubElement(test_xml,'base_dir', value=in_dir)
        # name = in_files_list[i_fold].split(args.out_val_xml[1])[0].split(args.out_val_xml[2])[0]
        SubElement(test_xml, 'subject', image=in_files_list[i_fold])#name + args.out_val_xml[1], labelmap=name + args.out_val_xml[2])


    f = open(args.out_val_xml[0], 'wb')
    f.write(ElementTree.tostring(folds_xml))
    f.close()


if args.out_tst_xml is not None:

    folds_xml = Element('folds')
    # SubElement(folds_xml, 'template_file', value=os.path.join(base_dir, 'processed', 'template.nii.gz'))

    fold_xml = SubElement(folds_xml, 'fold')

    # Train
    train_xml = SubElement(fold_xml, 'train')
    SubElement(train_xml,'base_dir', value=in_dir)

    for i in atlas_idx:
        # name = in_files_list[i].split(args.out_tst_xml[1])[0].split(args.out_tst_xml[2])[0]
        SubElement(train_xml, 'subject', image=in_files_list[i], index='{}'.format(i))#name + args.out_tst_xml[1], labelmap=name + args.out_tst_xml[2], index='{}'.format(i))

    # Test fold
    test_xml = SubElement(fold_xml, 'test')
    SubElement(test_xml,'base_dir', value=in_dir)

    for i in target_idx:
        # name = in_files_list[i].split(args.out_tst_xml[1])[0].split(args.out_tst_xml[2])[0]
        SubElement(test_xml, 'subject', image=in_files_list[i], index='{}'.format(i))#name + args.out_tst_xml[1], labelmap=name + args.out_tst_xml[2])


    f = open(args.out_tst_xml[0], 'wb')
    f.write(ElementTree.tostring(folds_xml))
    f.close()


if args.create_symlinks is not None:

    train_dir = args.create_symlinks[0] + '_train{}'.format(args.num_atlas[0])
    test_dir = args.create_symlinks[0] + '_test{}'.format(args.num_atlas[0])

    os.makedirs(train_dir)
    os.makedirs(test_dir)

    for i in atlas_idx:
        img_file = in_files_list[i].split(args.create_symlinks[4])[0] + args.create_symlinks[2]
        lab_file = in_files_list[i].split(args.create_symlinks[4])[0] + args.create_symlinks[3]
        os.symlink(os.path.join(args.create_symlinks[1], img_file ), os.path.join(train_dir, img_file))
        os.symlink(os.path.join(args.create_symlinks[1], lab_file ), os.path.join(train_dir, lab_file))

    for i in target_idx:
        img_file = in_files_list[i].split(args.create_symlinks[4])[0] + args.create_symlinks[2]
        lab_file = in_files_list[i].split(args.create_symlinks[4])[0] + args.create_symlinks[3]
        os.symlink(os.path.join(args.create_symlinks[1], img_file), os.path.join(test_dir, img_file))
        os.symlink(os.path.join(args.create_symlinks[1], lab_file), os.path.join(test_dir, lab_file))
