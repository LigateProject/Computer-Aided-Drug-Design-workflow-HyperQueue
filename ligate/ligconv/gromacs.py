from ..utils.paths import GenericPath
from ..utils.text import line_as_numbers
from .pose import Pose


def construct_additional_gromacs_files(
    pose: Pose,
    pose_number: int,
    gromacs_input: GenericPath,
    gromacs_output: GenericPath,
):
    """
    Constructs a .gro file from the provided pose and Gromacs input file.
    The `pose_number` will be stored as into the file.
    `pose_number` should start from 1.
    """
    assert pose_number >= 1

    coordinates = []
    for mol_line in pose.atoms.lines:
        values = line_as_numbers(mol_line, [2, 3, 4], float)
        values = [v / 10.0 for v in values]
        coordinates.append(values)

    with open(gromacs_input) as gromacs_in:
        with open(gromacs_output, "w") as gromacs_out:
            lines = gromacs_in.readlines()
            counter = -1
            for line in lines:
                if counter > 0:
                    line_list = line.split()
                    if line == lines[-1]:
                        gromacs_out.write(line)
                        break
                    else:
                        string = ""
                        for i in range(3):
                            string += line_list[i].rjust(5)
                        string += line_list[3].rjust(5)
                        for i in range(3):
                            string += f"{coordinates[counter - 1][i]:8.3f}"
                        string += "\n"
                        gromacs_out.write(string)
                elif counter == 0:
                    gromacs_out.write(line)
                else:
                    gromacs_out.write(f"Ligand pose {pose_number:5d}\n")
                counter += 1


def shift_last_gromacs_line(path: GenericPath, value: float):
    """
    Shifts the numbers in the last line of the gro file at `path` by `value`.
    The change is performed in-place.
    """
    line_offset = 0
    line_content = ""
    with open(path, "r+") as f:
        # Find the starting offset of the last line
        for line in f:
            line_offset += len(line_content)
            line_content = line
        values = line_content.split()
        values = [float(v) + value for v in values]
        values = " ".join(f"{v:11.5f}" for v in values)

        # Rewind before the last line
        f.seek(line_offset)
        f.write(f"{values}\n")
        # Remove the rest of the file
        f.truncate()


class ComplexGroFilePrinter:

    def __init__(self, filenameA, filenameB):
        f1 = open(filenameA, "r")
        f2 = open(filenameB, "r")

        # read in .gro files
        self.proteinGro = []
        self.mergedGro = []
        groFiles = [f1, f2]
        groFilesInMemory = [self.proteinGro, self.mergedGro]
        index = 0
        index2 = 2
        indices = [[2, 3, 6], [3, 4, 7]]
        for f in groFiles:
            groFilesInMemory[index].append("Protein in complex with merged ligand\n")
            lines = f.readlines()
            counter = 0
            for line in lines:
                if (counter > 0):
                    groFilesInMemory[index].append(line.split())
                    if (len(groFilesInMemory[index][-1]) == 1):
                        groFilesInMemory[index][-1] = int(groFilesInMemory[index][-1][0])
                    elif (line == lines[-1]):
                        groFilesInMemory[index][-1] = [float(groFilesInMemory[index][-1][i]) for i in range(len(groFilesInMemory[index][-1]))]
                    else:
                        if (len(groFilesInMemory[index][-1]) == 6):
                            index2 = 0
                        elif (len(groFilesInMemory[index][-1]) == 7):
                            index2 = 1
                        listToAppend = []
                        for i in range(indices[index2][0]):
                            listToAppend.append(groFilesInMemory[index][-1][i])
                        listToAppend.append(int(groFilesInMemory[index][-1][indices[index2][0]]))
                        for i in range(indices[index2][1], indices[index2][2]):
                            listToAppend.append(float(groFilesInMemory[index][-1][i]))
                        groFilesInMemory[index][-1] = listToAppend
                counter += 1
            index += 1

        f1.close()
        f2.close()

    def listToStringConverter(self, inputList):
        string = ""
        if (len(inputList) == 6):
            indices = [2, 3, 6]
            string += inputList[0].rjust(8)
            string += inputList[1].rjust(7)
        else:
            indices = [3, 4, 7]
            for i in range(3):
                string += inputList[i].rjust(5)
        string += "{:5d}".format(inputList[indices[0]])
        for i in range(indices[1], indices[2]):
            string += "{:8.3f}".format(inputList[i])
        string += "\n"
        return string

    def printComplexGroFile(self, filename):
        f1 = open(filename, "w")

        f1.write(self.proteinGro[0])
        f1.write("{:5d}\n".format(self.proteinGro[1] + self.mergedGro[1]))
        for i in range(2, len(self.proteinGro) - 1):
            f1.write(self.listToStringConverter(self.proteinGro[i]))
        for i in range(2, len(self.mergedGro) - 1):
            if (len(self.mergedGro[i]) == 6):
                self.mergedGro[i][2] += self.proteinGro[1]
            elif (len(self.mergedGro[i]) == 7):
                self.mergedGro[i][3] += self.proteinGro[1]
            f1.write(self.listToStringConverter(self.mergedGro[i]))
        string = ""
        for i in range(len(self.proteinGro[-1])):
            string += "{:11.5f}".format(self.proteinGro[-1][i])
            if i < len(self.proteinGro[-1]) - 1:
                string += " "
        string += "\n"
        f1.write(string)

        f1.close()


def write_gro_complex_structure(
        protein_structure: GenericPath,
        ligand_structure: GenericPath,
        complex_structure: GenericPath
):
    """
    Writes the complex structure from a protein and ligand structure into `complex_structure`.
    """
    printer = ComplexGroFilePrinter(str(protein_structure), str(ligand_structure))
    printer.printComplexGroFile(str(complex_structure))
