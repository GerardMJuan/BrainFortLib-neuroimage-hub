#!/bin/bash
export SPM_DIR=/homedtic/gmarti/LIB/spm12
export SPM_EXEC=/homedtic/gmarti/LIB/spm12/bin/spm12-matlab
exec ${SPM_EXEC} script ${SPM_DIR}/spm_BIDS_App.m $@
