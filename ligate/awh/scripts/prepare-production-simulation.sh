#!/bin/bash

### Inputs
# CADD_SCRIPTS_DIR - path to the directory with CADD scripts
# GROMACS - path to a GROMACS `gmx` file
# MDP_FILE - path to a production.mdp file

### Input directory
# Expects to be executed in a directory that contains edge_lig_35_L_lig_34_L... directories with
# pose_0 subdirectories.
# After execution, prepared TODO.

set -ue

PATH_TO_SCRIPTS=${CADD_SCRIPTS_DIR}

target=$(pwd | rev | cut -d "/" -f 1 | rev)

# check equilibration results and clean up first
for edge in edge_*; do
cd ${edge}
for pose in pose_*; do
cd ${pose}

## error catching
## The final .gro file of the equilibration must exist
if ! [ -f equiNVT_complex.gro ]
then
  echo "For ${pose} of ${edge}, the complex could not be equilibrated. Deleting folder!"
  exit 1
#cd ..
#rm -rf ${OUTPUT_PATH}/${target}/${edge}/${pose}
#continue
fi
if ! [ -f equiNVT_ligand.gro ]
then
  echo "For ${pose} of ${edge}, the ligand could not be equilibrated. Deleting folder!"
  exit 1
#cd ..
#rm -rf ${OUTPUT_PATH}/${target}/${edge}/${pose}
#continue
fi

mv equiNVT_complex.gro start_complex.gro
mv equiNVT_ligand.gro start_ligand.gro
rm ions_complex.gro ions_ligand.gro equi* slurm-*

cd ..
done # poses

echo "foo"

# remove directory if none of the poses survives
if (( $(ls -lh ${edge} | grep "pose_" | wc -l) == 0 ));
then
echo "For ${edge}, the equilibration was not successful for any of the poses. Deleting directory!"
cd ..
rm -rf ${edge}
continue
fi

cd ..
done # edges

# remove directory if none of the edges survives
if (( $(ls -lh ${target} | grep "edge_" | wc -l) == 0 ));
then
echo "The equilibration was not successful for any of the edges. Stopping workflow execution!"
cd ..
rm -rf ${target}
exit 0
fi

for edge in edge_*; do
cd ${edge}
for pose in pose_*; do
cd ${pose}

# make sure masses are not changed because this is not supported with AWH
python3 ${PATH_TO_SCRIPTS}/fixMassesForAWH.py
mv mergedConstantMass.itp merged.itp

# run grompp to get input .tpr file
# ignore warning about perturbed constraints
${GROMACS} grompp -f ${MDP_FILE} -c start_complex.gro -p topol_amber.top -o production_complex.tpr -po productionOut_complex.mdp -maxwarn 1 || true
${GROMACS} grompp -f ${MDP_FILE} -c start_ligand.gro -p topol_ligandInWater.top -o production_ligand.tpr -po productionOut_ligand.mdp -maxwarn 1 || true
## error catching
## TPR file for production simulation must exist
if ! [ -f production_complex.tpr ]
then
echo "For ${pose} of ${edge}, the TPR file could not be generated for the complex (grompp error). Deleting folder!"
cd ..
rm -rf ${pose}
continue
fi
if ! [ -f production_ligand.tpr ]
then
echo "For ${pose} of ${edge}, the TPR file could not be generated for the ligand (grompp error). Deleting folder!"
cd ..
rm -rf ${pose}
continue
fi

rm productionOut_complex.mdp
rm productionOut_ligand.mdp

echo "For ${pose} of ${edge}, the TPR file has been generated successfully."

cd ..
done # poses

# remove directory if none of the poses survives
if (( $(ls -lh | grep "pose_" | wc -l) == 0 ));
then
echo "For ${edge}, the TPR file could not be generated successfully for any of the poses. Deleting directory!"
exit 1
cd ..
rm -rf ${edge}
continue
fi

cd ..
done # edges

# remove directory if none of the edges survives
if (( $(ls -lh | grep "edge_" | wc -l) == 0 ));
then
echo "The TPR file could not be generated successfully for any of the edges. Stopping workflow execution!"
cd ..
#rm -rf ${target}
exit 1
fi

echo "${target} successfully completed!"
