#!/bin/bash

### Inputs
# CADD_SCRIPTS_DIR - path to the directory with CADD scripts

### Input directory
# Expects to be executed in a directory that contains lig_... directories with pose_0
# subdirectories.
# After execution, deletes most of the current directory and creates e.g. edge_lig_35_L_lig_34_L.

set -ue

target=$(pwd | rev | cut -d "/" -f 1 | rev)

PATH_TO_SCRIPTS=${CADD_SCRIPTS_DIR}

echo "Creating hybrid ligands for ${target} ..."

# run ligand pairing script
cp ${PATH_TO_SCRIPTS}/CB_ligand_pairing_v4.py .
cp ${PATH_TO_SCRIPTS}/MCS_sebastian.py .

python3 CB_ligand_pairing_v4.py

if ! [ -f ligandPairs.json ]
then
echo "Ligand pairing was completely unsuccessful. Stopping workflow execution!"
exit 1
fi

ligands1=($(grep "Ligand_1" ligandPairs.json | cut -d "\"" -f 4 | cut -d "/" -f 2))
ligands2=($(grep "Ligand_2" ligandPairs.json | cut -d "\"" -f 4 | cut -d "/" -f 2))

# clean up
rm -r CB_ligand_pairing_v4.py MCS_sebastian.py __pycache__

# merge topologies for pairs of ligands
for index in $(seq 0 $(( ${#ligands1[@]}-1 ))); do

mkdir edge_${ligands1[${index}]}_${ligands2[${index}]}
cd edge_${ligands1[${index}]}_${ligands2[${index}]}

#TODO: avoid repeating topology merge; can end up with different hybrid ligands between replicas now
for i in 0 1; do
for j in 0 1; do
# list input files
## pair pose 0 with pose 0 and pose 1 with pose 1
## but make sure that both ligands dominate the initial coordinates once for each pose pair
if (( j == 0 ))
then
file1=../../${ligands1[${index}]}/ligand_premature.itp
file2=../../${ligands2[${index}]}/ligand_premature.itp
file3=../../${ligands1[${index}]}/pose_${i}/ligand.mol2
file4=../../${ligands2[${index}]}/pose_${i}/ligand.mol2
file5=../../${ligands1[${index}]}/pose_${i}/ligand.gro
file6=../../${ligands2[${index}]}/pose_${i}/ligand.gro
elif (( j == 1 ))
then
file1=../../${ligands2[${index}]}/ligand_premature.itp
file2=../../${ligands1[${index}]}/ligand_premature.itp
file3=../../${ligands2[${index}]}/pose_${i}/ligand.mol2
file4=../../${ligands1[${index}]}/pose_${i}/ligand.mol2
file5=../../${ligands2[${index}]}/pose_${i}/ligand.gro
file6=../../${ligands1[${index}]}/pose_${i}/ligand.gro
fi

mkdir pose_${i}_${j}
cd pose_${i}_${j}

# merge topologies and .gro files
python3 $PATH_TO_SCRIPTS/mergeTopologies.py <<-eof
$file1
$file2
$file3
$file4
merged.itp
$file5
$file6
merged.gro
eof

# write topology summary
python3 $PATH_TO_SCRIPTS/writeTopologySummary.py

# print .gro file for complex of protein and hybrid ligand
python3 $PATH_TO_SCRIPTS/printComplexGroFile.py <<-eof
../../conf.gro
merged.gro
full.gro
eof

# print position restraints file for ligand
python3 $PATH_TO_SCRIPTS/posResForLigand.py 

# make sure masses are not changed because this is not supported with AWH
python3 ${PATH_TO_SCRIPTS}/fixMassesForAWH.py
mv mergedConstantMass.itp merged.itp

# include position restraints for protein correctly
for file in *; do
if grep -q "posre" ${file} && ! grep -q "posre_ligand" ${file}
then
sed -i ${file} -e "s=posre=../../posre=g"
fi
done

cd ..
done
done

# remove directory if none of the poses survives
if (( $(ls -lh | grep "pose_" | wc -l) < 1 ));
then
echo "For edge_${ligands1[${index}]}_${ligands2[${index}]}, no hybrid ligand poses could be generated. Deleting directory!"
cd ..
rm -rf edge_${ligands1[${index}]}_${ligands2[${index}]}
continue
fi

cd ..
done

# clean up
rm topol.top conf.gro
for lig in $(ls -d */ | grep -v "edge"); do
rm -r ${lig}
done
