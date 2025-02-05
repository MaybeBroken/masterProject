# This script reads a file and generates a blender model based off of the file

import os
import sys
import csv

with open("file.csv") as file:
    data = file.readlines()

with open("file.csv", "w") as file:
    file.writelines(
        line
        for line in data
        if line != ",,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,\n"
    )


file = csv.reader(open("file.csv"))

fileData = []

for row in file:
    _row = []
    for column in row:
        _row.append(column)
    fileData.append(_row)

print(fileData)