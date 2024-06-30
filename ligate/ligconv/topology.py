import sys

from rdkit import Chem
from rdkit.Chem import rdMolAlign, rdmolops

from ..utils.io import check_has_extension
from ..utils.paths import GenericPath
from .common import ProteinForcefield, WaterModel


class TopologyMerger:
    def __init__(self, filename1, filename2):
        f1 = open(filename1, "r")
        f2 = open(filename2, "r")
        self.f1 = f1.readlines()
        self.f2 = f2.readlines()
        self.f = [self.f1, self.f2]
        f1.close()
        f2.close()

    def readInAtomTypes(self):
        # read in the corresponding part of the topology
        self.atomtypes = []
        index = 0
        for f in self.f:
            self.atomtypes.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[1] == "atomtypes":
                        check1 = True
                    elif line.split()[1] == "moleculetype":
                        check2 = False
                        break
                    if check1 and check2:
                        self.atomtypes[index].append(line)
            index += 1

    def readInHeaders(self):
        # read in the corresponding part of the topology
        self.header = []
        index = 0
        for f in self.f:
            self.header.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[1] == "moleculetype":
                        check1 = True
                    elif line.split()[1] == "atoms":
                        check2 = False
                        break
                    if check1 and check2:
                        self.header[index].append(line)
            index += 1

    def readInAtoms(self):
        # read in the atoms section of the topology
        self.atoms = []
        index = 0
        for f in self.f:
            self.atoms.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[1] == "bonds":
                        check2 = False
                        break
                    if check1 and check2 and line.split()[0] != ";":
                        indexCut = line.split().index(";")
                        self.atoms[index].append(line.split()[:indexCut])
                    if line.split()[1] == "atoms":
                        check1 = True
            index += 1

    def readInBonds(self):
        # read in the bonds section of the topology
        self.bonds = []
        index = 0
        for f in self.f:
            self.bonds.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[1] == "pairs":
                        check2 = False
                        break
                    if check1 and check2 and line.split()[0] != ";":
                        indexCut = line.split().index(";")
                        self.bonds[index].append(line.split()[:indexCut])
                    if line.split()[1] == "bonds":
                        check1 = True
            index += 1

    def readInPairs(self):
        # read in the pairs section of the topology
        self.pairs = []
        index = 0
        for f in self.f:
            self.pairs.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[1] == "angles":
                        check2 = False
                        break
                    if check1 and check2 and line.split()[0] != ";":
                        indexCut = line.split().index(";")
                        self.pairs[index].append(line.split()[:indexCut])
                    if line.split()[1] == "pairs":
                        check1 = True
            index += 1

    def readInAngles(self):
        # read in the angles section of the topology
        self.angles = []
        index = 0
        for f in self.f:
            self.angles.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[1] == "dihedrals":
                        check2 = False
                        break
                    if check1 and check2 and line.split()[0] != ";":
                        indexCut = line.split().index(";")
                        self.angles[index].append(line.split()[:indexCut])
                    if line.split()[1] == "angles":
                        check1 = True
            index += 1

    def readInDihedrals(self):
        # read in the dihedrals section of the topology
        self.dihedrals = []
        index = 0
        for f in self.f:
            self.dihedrals.append([])
            check1 = False
            check2 = True
            for line in f:
                if len(line.split()) >= 2:
                    if line.split()[0] == "#ifdef":
                        check2 = False
                    if check1 and check2 and line.split()[0] != ";" and line.split()[0] != "[":
                        indexCut = line.split().index(";")
                        self.dihedrals[index].append(line.split()[:indexCut])
                    if line.split()[1] == "dihedrals":
                        check1 = True
            index += 1

    def readInData(self):
        self.readInAtomTypes()
        self.readInHeaders()
        self.readInAtoms()
        self.readInBonds()
        self.readInPairs()
        self.readInAngles()
        self.readInDihedrals()

    def createMapping(self, filename1, filename2):
        # let rdkit align the two molecules
        ligandA = rdmolops.AddHs(Chem.MolFromMol2File(filename1))
        ligandB = rdmolops.AddHs(Chem.MolFromMol2File(filename2))
        o3a = rdMolAlign.GetO3A(ligandA, ligandB)
        mapping = o3a.Matches()

        # we can assume that the order of atoms is the same in mol2 and itp file
        # rdkit only aligns heavy atoms; add hydrogens back
        numberMapping = []
        for i in range(len(self.atoms)):
            numberMapping.append([])
            for j in range(len(self.atoms[i])):
                if "h" not in self.atoms[i][j][1]:
                    numberMapping[i].append(j)
        for i in range(len(mapping)):
            for j in range(len(mapping[i])):
                mapping[i][j] = numberMapping[j][i]

        # identify hydrogens bound to heavy atoms
        for i in range(len(mapping)):
            boundHydrogens = []
            numberHydrogens = []
            for j in range(len(mapping[i])):
                boundHydrogens.append([])
                for k in range(len(self.bonds[j])):
                    if mapping[i][j] == int(self.bonds[j][k][0]) - 1:
                        if "h" in self.atoms[j][int(self.bonds[j][k][1]) - 1][1]:
                            boundHydrogens[j].append(int(self.bonds[j][k][1]) - 1)
                    elif mapping[i][j] == int(self.bonds[j][k][1]) - 1:
                        if "h" in self.atoms[j][int(self.bonds[j][k][0]) - 1][1]:
                            boundHydrogens[j].append(int(self.bonds[j][k][0]) - 1)
                boundHydrogens[j].sort()
                numberHydrogens.append(len(boundHydrogens[j]))
            for k in range(min(numberHydrogens)):
                listToAppend = []
                for j in range(len(boundHydrogens)):
                    listToAppend.append(boundHydrogens[j][k])
                mapping.append(listToAppend)

        # add dummy atoms
        covered = [[] for i in range(len(self.atoms))]
        for i in range(len(mapping)):
            for j in range(len(mapping[i])):
                covered[j].append(mapping[i][j])
        for i in range(len(self.atoms)):
            for j in range(len(self.atoms[i])):
                if j not in covered[i]:
                    if i == 0:
                        mapping.append([j, "DUM"])
                    else:
                        mapping.append(["DUM", j])

        # index mapping between ligand A and B and the hybrid ligand
        indexMapping = [[] for i in range(len(self.atoms))]
        # we stick to the order of atoms in ligand A
        indexMapping[0] = [i for i in range(len(self.atoms[0]))]
        # order atoms in ligand B such that they align to the order of atoms in ligand A
        # add additional atoms at the end
        for i in range(1, len(self.atoms)):
            count = 0
            for j in range(len(self.atoms[i])):
                for k in range(len(mapping)):
                    if int(self.atoms[i][j][0]) - 1 == mapping[k][i]:
                        if mapping[k][0] != "DUM":
                            indexMapping[i].append(mapping[k][0])
                        else:
                            indexMapping[i].append(len(self.atoms[0]) + count)
                            count += 1
                        break
        self.indexMapping = indexMapping

    def mergeHeaders(self):
        # merge data
        self.header.append([])
        for i in range(len(self.header[0]) - 1):
            if self.header[0][i] == self.header[1][i]:
                self.header[-1].append(self.header[0][i])
            else:
                sys.exit("Topology headers are assumed to be identical, but they aren't.")
        self.header[-1].append("MOL  3\n")

    def mergeAtoms(self):
        # merge data
        self.dummyAtoms = []
        self.atoms.append([])
        self.atoms[-1].append(" [ atoms ]\n")
        self.atoms[-1].append(
            ";   nr       type  resnr residue  atom   cgnr     charge       mass  typeB    "
            "chargeB      massB\n"
        )
        justificationList = [6, 12, 7, 7, 7, 7, 11, 11, 12, 11, 11]
        for i in range(max(self.indexMapping[-1]) + 1):
            resultString = ""
            if i < len(self.atoms[0]):
                for j in range(len(self.atoms[0][i])):
                    resultString += self.atoms[0][i][j].rjust(justificationList[j], " ")
                if i in self.indexMapping[1]:
                    checkCount = 0
                    indexList = [1, 6, 7]
                    for j in range(3):
                        if (
                            self.atoms[0][i][indexList[j]]
                            != self.atoms[1][self.indexMapping[1].index(i)][indexList[j]]
                        ):
                            checkCount += 1
                    if checkCount > 0:
                        for j in range(3):
                            resultString += self.atoms[1][self.indexMapping[1].index(i)][
                                indexList[j]
                            ].rjust(justificationList[len(self.atoms[0][i]) + j], " ")
                else:
                    if "DUM_" + self.atoms[0][i][1] not in self.dummyAtoms:
                        self.dummyAtoms.append("DUM_" + self.atoms[0][i][1])
                    resultString += ("DUM_" + self.atoms[0][i][1]).rjust(12)
                    resultString += "0.000000".rjust(11)
                    # need to worry about masses for virtual sites later
                    resultString += self.atoms[0][i][7].rjust(11)
            else:
                if "DUM_" + self.atoms[1][self.indexMapping[1].index(i)][1] not in self.dummyAtoms:
                    self.dummyAtoms.append("DUM_" + self.atoms[1][self.indexMapping[1].index(i)][1])
                resultString += str(i + 1).rjust(6)
                resultString += ("DUM_" + self.atoms[1][self.indexMapping[1].index(i)][1]).rjust(12)
                for j in range(2, 4):
                    resultString += self.atoms[1][self.indexMapping[1].index(i)][j].rjust(
                        justificationList[j], " "
                    )
                resultString += ("D" + self.atoms[1][self.indexMapping[1].index(i)][4]).rjust(
                    justificationList[4], " "
                )
                resultString += str(i + 1).rjust(justificationList[5], " ")
                resultString += "0.000000".rjust(11)
                # need to worry about masses for virtual sites later
                resultString += self.atoms[1][self.indexMapping[1].index(i)][7].rjust(11)
                resultString += self.atoms[1][self.indexMapping[1].index(i)][1].rjust(12)
                for j in range(
                    len(self.atoms[1][self.indexMapping[1].index(i)]) - 2,
                    len(self.atoms[1][self.indexMapping[1].index(i)]),
                ):
                    resultString += self.atoms[1][self.indexMapping[1].index(i)][j].rjust(
                        justificationList[j], " "
                    )
            resultString += "\n"
            self.atoms[-1].append(resultString)

    def mergeBonds(self):
        # merge data
        self.bonds.append([])
        self.bonds[-1].append(" [ bonds ]\n")
        self.bonds[-1].append(
            ";  ai    aj funct            c0            c1            c2            c3\n"
        )
        justificationList = [6, 7, 7, 15, 15, 15, 15]
        alreadySeen = []
        for i in range(len(self.bonds[0])):
            alreadySeen.append(
                [
                    (self.bonds[0][i][0], self.bonds[0][i][1]),
                    self.bonds[0][i][2],
                    self.bonds[0][i][3],
                    self.bonds[0][i][4],
                    self.bonds[0][i][3],
                    self.bonds[0][i][4],
                ]
            )
        alreadySeenTuples = [tuple(map(int, alreadySeen[i][0])) for i in range(len(alreadySeen))]
        for i in range(len(self.bonds[1])):
            testTuple = (
                self.indexMapping[1][int(self.bonds[1][i][0]) - 1] + 1,
                self.indexMapping[1][int(self.bonds[1][i][1]) - 1] + 1,
            )
            if testTuple in alreadySeenTuples:
                alreadySeen[alreadySeenTuples.index(testTuple)][-2] = self.bonds[1][i][3]
                alreadySeen[alreadySeenTuples.index(testTuple)][-1] = self.bonds[1][i][4]
            else:
                alreadySeen.append(
                    [
                        tuple(map(str, testTuple)),
                        self.bonds[1][i][2],
                        self.bonds[1][i][3],
                        self.bonds[1][i][4],
                        self.bonds[1][i][3],
                        self.bonds[1][i][4],
                    ]
                )
        for i in range(len(alreadySeen)):
            resultString = ""
            resultString += alreadySeen[i][0][0].rjust(justificationList[0]) + alreadySeen[i][0][
                1
            ].rjust(justificationList[1])
            resultString += alreadySeen[i][1].rjust(justificationList[2])
            for j in range(2, len(alreadySeen[i])):
                resultString += ("{:.6f}".format(float(alreadySeen[i][j]))).rjust(
                    justificationList[j + 1]
                )
            resultString += "\n"
            self.bonds[-1].append(resultString)

    def mergePairs(self):
        # merge data
        self.pairs.append([])
        self.pairs[-1].append(" [ pairs ]\n")
        self.pairs[-1].append(
            ";  ai    aj funct            c0            c1            c2            c3\n"
        )
        justificationList = [6, 7, 7]
        alreadySeen = []
        for i in range(len(self.pairs[0])):
            alreadySeen.append([(self.pairs[0][i][0], self.pairs[0][i][1]), self.pairs[0][i][2]])
        alreadySeenTuples = [tuple(map(int, alreadySeen[i][0])) for i in range(len(alreadySeen))]
        for i in range(len(self.pairs[1])):
            testTuple = (
                self.indexMapping[1][int(self.pairs[1][i][0]) - 1] + 1,
                self.indexMapping[1][int(self.pairs[1][i][1]) - 1] + 1,
            )
            if testTuple not in alreadySeenTuples:
                alreadySeen.append([tuple(map(str, testTuple)), self.pairs[1][i][2]])
        for i in range(len(alreadySeen)):
            resultString = ""
            resultString += alreadySeen[i][0][0].rjust(justificationList[0]) + alreadySeen[i][0][
                1
            ].rjust(justificationList[1])
            resultString += alreadySeen[i][1].rjust(justificationList[2])
            resultString += "\n"
            self.pairs[-1].append(resultString)

    def mergeAngles(self):
        # merge data
        self.angles.append([])
        self.angles[-1].append(" [ angles ]\n")
        self.angles[-1].append(
            ";  ai    aj    ak funct            c0            c1            c2            c3\n"
        )
        justificationList = [6, 7, 7, 7, 15, 15, 15, 15]
        alreadySeen = []
        for i in range(len(self.angles[0])):
            alreadySeen.append(
                [
                    (self.angles[0][i][0], self.angles[0][i][1], self.angles[0][i][2]),
                    self.angles[0][i][3],
                    self.angles[0][i][4],
                    self.angles[0][i][5],
                    self.angles[0][i][4],
                    self.angles[0][i][5],
                ]
            )
        alreadySeenTuples = [tuple(map(int, alreadySeen[i][0])) for i in range(len(alreadySeen))]
        for i in range(len(self.angles[1])):
            testTuple = (
                self.indexMapping[1][int(self.angles[1][i][0]) - 1] + 1,
                self.indexMapping[1][int(self.angles[1][i][1]) - 1] + 1,
                self.indexMapping[1][int(self.angles[1][i][2]) - 1] + 1,
            )
            if testTuple in alreadySeenTuples:
                alreadySeen[alreadySeenTuples.index(testTuple)][-2] = self.angles[1][i][4]
                alreadySeen[alreadySeenTuples.index(testTuple)][-1] = self.angles[1][i][5]
            else:
                alreadySeen.append(
                    [
                        tuple(map(str, testTuple)),
                        self.angles[1][i][3],
                        self.angles[1][i][4],
                        self.angles[1][i][5],
                        self.angles[1][i][4],
                        self.angles[1][i][5],
                    ]
                )
        for i in range(len(alreadySeen)):
            resultString = ""
            resultString += (
                alreadySeen[i][0][0].rjust(justificationList[0])
                + alreadySeen[i][0][1].rjust(justificationList[1])
                + alreadySeen[i][0][2].rjust(justificationList[2])
            )
            resultString += alreadySeen[i][1].rjust(justificationList[3])
            for j in range(2, len(alreadySeen[i])):
                resultString += ("{:.6f}".format(float(alreadySeen[i][j]))).rjust(
                    justificationList[j + 2]
                )
            resultString += "\n"
            self.angles[-1].append(resultString)

    def mergeDihedrals(self):
        # merge data
        self.dihedrals.append([])
        self.dihedrals[-1].append(" [ dihedrals ]\n")
        self.dihedrals[-1].append(
            ";  ai    aj    ak    al funct            c0            c1            c2            "
            "c3            c4            c5\n"
        )
        justificationList = [6, 7, 7, 7, 5]
        alreadySeen = []
        for i in range(len(self.dihedrals[0])):
            listToAppend = []
            listToAppend.append(
                (
                    self.dihedrals[0][i][0],
                    self.dihedrals[0][i][1],
                    self.dihedrals[0][i][2],
                    self.dihedrals[0][i][3],
                )
            )
            for j in range(4, 8):
                listToAppend.append(self.dihedrals[0][i][j])
            for j in range(5, 8):
                listToAppend.append(self.dihedrals[0][i][j])
            listToAppend[6] = "0"  # why?
            alreadySeen.append(listToAppend)
        for i in range(len(self.dihedrals[1])):
            listToAppend = []
            testTuple = [
                self.indexMapping[1][int(self.dihedrals[1][i][j]) - 1] + 1 for j in range(4)
            ]
            listToAppend.append(tuple(map(str, testTuple)))
            for j in range(4, 8):
                listToAppend.append(self.dihedrals[1][i][j])
            for j in range(5, 8):
                listToAppend.append(self.dihedrals[1][i][j])
            listToAppend[3] = "0"  # why?
            alreadySeen.append(listToAppend)
        for i in range(len(alreadySeen)):
            resultString = ""
            for j in range(4):
                resultString += alreadySeen[i][0][j].rjust(justificationList[j])
            resultString += alreadySeen[i][1].rjust(justificationList[4])
            for j in range(2, len(alreadySeen[i])):
                if int(float(alreadySeen[i][j])) == float(alreadySeen[i][j]):
                    resultString += " " + str(int(float(alreadySeen[i][j])))
                else:
                    resultString += " " + alreadySeen[i][j]
            resultString += "\n"
            self.dihedrals[-1].append(resultString)
            check = False
            if ("DUM" in self.atoms[-1][int(alreadySeen[i][0][0]) + 1]) or (
                "DUM" in self.atoms[-1][int(alreadySeen[i][0][3]) + 1]
            ):
                check = True
            if check:
                if (
                    (i < len(self.dihedrals[0]))
                    and (int(alreadySeen[i][1]) == 4)
                    and (float(alreadySeen[i][3]) > 0)
                    and (float(alreadySeen[i][6]) == 0)
                ):
                    alreadySeen[i][3] = "0"  # why?
                elif (
                    (i >= len(self.dihedrals[0]))
                    and (int(alreadySeen[i][1]) == 4)
                    and (float(alreadySeen[i][3]) == 0)
                    and (float(alreadySeen[i][6]) > 0)
                ):
                    alreadySeen[i][6] = "0"  # why?
                else:
                    alreadySeen[i][3], alreadySeen[i][6] = (
                        alreadySeen[i][6],
                        alreadySeen[i][3],
                    )
                resultString = ""
                for j in range(4):
                    resultString += alreadySeen[i][0][j].rjust(justificationList[j])
                resultString += alreadySeen[i][1].rjust(justificationList[4])
                for j in range(2, len(alreadySeen[i])):
                    if int(float(alreadySeen[i][j])) == float(alreadySeen[i][j]):
                        resultString += " " + str(int(float(alreadySeen[i][j])))
                    else:
                        resultString += " " + alreadySeen[i][j]
                resultString += "\n"
                self.dihedrals[-1].append(resultString)

    def mergeData(self):
        self.mergeHeaders()
        self.mergeAtoms()
        self.mergeBonds()
        self.mergePairs()
        self.mergeAngles()
        self.mergeDihedrals()

    def printTopology(self, filename):
        f = open(filename, "w")
        components = [
            self.header,
            self.atoms,
            self.bonds,
            self.pairs,
            self.angles,
            self.dihedrals,
        ]
        count = 0
        for line in components:
            for i in range(len(line[-1])):
                f.write(line[-1][i])
            count += 1
            if count < len(components):
                f.write("\n")
        f.write("\n")
        f.write("; Include Position restraint file\n")
        f.write("#ifdef POSRES\n")
        f.write('#include "posre_Ligand.itp"\n')
        f.write("#endif\n")
        f.close()

    def generateAtomTypesFile(self, directory: GenericPath):
        with open(directory / "ffMOL.itp", "w") as f:
            for i in range(len(self.atomtypes[0])):
                f.write(self.atomtypes[0][i])
            for i in range(len(self.atomtypes[1])):
                if self.atomtypes[1][i] not in self.atomtypes[0]:
                    f.write(self.atomtypes[1][i])
            for i in range(len(self.dummyAtoms)):
                string = " "
                for j in range(2):
                    string += self.dummyAtoms[i].ljust(9)
                string += " "
                for j in range(2):
                    string += "0.00000".rjust(9)
                string += "A".rjust(4) + "  "
                for j in range(2):
                    string += "0.00000e+00".rjust(14)
                string += "\n"
                f.write(string)

    def writeFirstGroFile(self, outputFile, groFileList):
        for i in range(len(groFileList[0]) - 1):
            if i == 0:
                outputFile.write(groFileList[0][0])
            elif i == 1:
                outputFile.write(" {:d}\n".format(max(self.indexMapping[-1]) + 1))
            else:
                string = ""
                for j in range(3):
                    string += groFileList[0][i][j].rjust(5)
                string += "{:5d}".format(groFileList[0][i][3])
                for j in range(4, 7):
                    string += "{:8.3f}".format(groFileList[0][i][j])
                string += "\n"
                outputFile.write(string)

    def printAtomsFromSecondGroFile(self, indexList, outputFile, groFileList):
        for i in indexList:
            index = self.indexMapping[1].index(i) + 2
            string = ""
            groFileList[1][index][2] = "D" + groFileList[1][index][2]
            for j in range(3):
                string += groFileList[1][index][j].rjust(5)
            string += "{:5d}".format(i + 1)
            for j in range(4, 7):
                string += "{:8.3f}".format(groFileList[1][index][j])
            string += "\n"
            outputFile.write(string)

    def mergeLigandGroFiles(self, filenameA, filenameB, filenameC):
        f1 = open(filenameA, "r")
        f2 = open(filenameB, "r")
        f3 = open(filenameC, "w")

        # read in .gro files
        gro = []
        index = 0
        for f in [f1, f2]:
            gro.append([])
            lines = f.readlines()
            counter = 0
            for line in lines:
                if counter > 0:
                    gro[index].append(line.split())
                    if len(gro[index][-1]) == 1:
                        gro[index][-1] = int(gro[index][-1][0])
                    elif line == lines[-1]:
                        gro[index][-1] = [
                            float(gro[index][-1][i]) for i in range(len(gro[index][-1]))
                        ]
                    else:
                        gro[index][-1] = [
                            gro[index][-1][0],
                            gro[index][-1][1],
                            gro[index][-1][2],
                            int(gro[index][-1][3]),
                            float(gro[index][-1][4]),
                            float(gro[index][-1][5]),
                            float(gro[index][-1][6]),
                        ]
                else:
                    gro[index].append("Merged ligand\n")
                counter += 1
            index += 1

        # write merged .gro file
        # atoms from first .gro file
        self.writeFirstGroFile(f3, gro)
        # additional atoms from the second .gro file (all virtual sites)
        indexList = range(len(self.atoms[0]), max(self.indexMapping[-1]) + 1)
        self.printAtomsFromSecondGroFile(indexList, f3, gro)
        # last line of first .gro file
        string = ""
        for j in range(len(gro[0][-1])):
            string += "{:11.5f}".format(gro[0][-1][j])
            if j < len(gro[0][-1]) - 1:
                string += " "
        string += "\n"
        f3.write(string)

        f1.close()
        f2.close()
        f3.close()


def merge_topologies(
    ligand_a_topology: GenericPath,
    ligand_a_structure_mol2: GenericPath,
    ligand_a_structure_gro: GenericPath,
    ligand_b_topology: GenericPath,
    ligand_b_structure_mol2: GenericPath,
    ligand_b_structure_gro: GenericPath,
    output_merged_topology: GenericPath,
    output_merged_structure: GenericPath,
):
    check_has_extension(ligand_a_topology, "itp")
    check_has_extension(ligand_a_structure_mol2, "mol2")
    check_has_extension(ligand_a_structure_gro, "gro")
    check_has_extension(ligand_b_topology, "itp")
    check_has_extension(ligand_b_structure_mol2, "mol2")
    check_has_extension(ligand_b_structure_gro, "gro")

    tm = TopologyMerger(str(ligand_a_topology), str(ligand_b_topology))
    tm.readInData()
    tm.createMapping(str(ligand_a_structure_mol2), str(ligand_b_structure_mol2))
    tm.mergeData()
    tm.printTopology(str(output_merged_topology))
    # TODO: the ffMOL.itp file has to be in the same directory as the other topologies, this is
    # currently not enforced
    tm.generateAtomTypesFile(output_merged_topology.parent)
    tm.mergeLigandGroFiles(
        str(ligand_a_structure_gro),
        str(ligand_b_structure_gro),
        str(output_merged_structure),
    )


def write_topology_summary(
    topology: GenericPath,
    topology_ligand_in_water: GenericPath,
    topology_amber: GenericPath,
    forcefield_path: GenericPath,
):
    with open(topology_ligand_in_water, "w") as f:
        f.write(
            f"""; Include forcefield parameters
#include "{forcefield_path}/forcefield.itp"
#include "ffMOL.itp"

; Include ligand topology
#include "merged.itp"

; Include water topology
#include "{forcefield_path}/tip3p.itp"

; Include topology for ions
#include "{forcefield_path}/ions.itp"

[ system ]
; Name
ligand in water

[ molecules ]
; Compound        #mols
MOL 1
"""
        )

    with open(topology) as topology_file:
        check = False
        counter = 0

        with open(topology_amber, "w") as target:
            for line in topology_file:
                if line == "; Include forcefield parameters\n":
                    check = True
                    counter = 0
                if line == "; Include water topology\n":
                    target.write(
                        """; Include ligand topology
#include "merged.itp"

"""
                    )
                if check:
                    if line == "Protein\n":
                        target.write("Protein-ligand complex in water\n")
                        continue
                    target.write(line)
                    counter += 1
                    if counter == 2:
                        target.write('#include "ffMOL.itp"\n')

            target.write("MOL 1\n")


def pos_res_for_ligand_to_fix_structure(topology: GenericPath, posre_ligand: GenericPath):
    with open(topology) as f:
        with open(posre_ligand, "w") as target:
            check = -2
            target.write(
                """[ position_restraints ]
; atom  type      fx      fy      fz
"""
            )

            # I don't want any of the atoms of A to move
            value = 100000

            for line in f:
                data = line.split()
                if check == 0:
                    if len(data) > 1:
                        if data[1] == "bonds":
                            check = -2
                        elif "DUM" not in data[1]:
                            target.write(f"{int(data[0]):6}{1:6}{value:8}{value:8}{value:8}\n")
                elif check == -1:
                    check = 0
                elif len(data) > 1:
                    if data[1] == "atoms":
                        check = -1


def pos_res_for_ligand(topology: GenericPath, posre_ligand: GenericPath):
    with open(topology) as f:
        with open(posre_ligand, "w") as target:
            check = -2
            target.write(
                """[ position_restraints ]
; atom  type      fx      fy      fz
"""
            )

            for line in f:
                data = line.split()
                if check == 0:
                    if len(data) > 1:
                        if data[1] == "bonds":
                            check = -2
                        elif "h" not in data[1] and "H" not in data[1]:
                            # TODO: why 8 above and 6 here?
                            target.write(f"{int(data[0]):6}{1:6}{1000:6}{1000:6}{1000:6}\n")
                elif check == -1:
                    check = 0
                elif len(data) > 1:
                    if data[1] == "atoms":
                        check = -1


def protein_ff_gromacs_code(forcefield: ProteinForcefield) -> int:
    if forcefield == ProteinForcefield.Amber99SB_ILDN:
        return 6
    else:
        assert False


def water_model_gromacs_code(model: WaterModel) -> int:
    if model == WaterModel.Tip3p:
        return 1
    else:
        assert False
