import pandas as pd
from getdata import getdata

# input is either 'regular' or 'vandalism'
PATH = input()
print('processing ' + PATH + '...')
if (PATH == "regular"):
    FOLDER_NAME = "wikidata_reg/"
else:
    FOLDER_NAME = "wikidata_van/"

TRUNCATE = False
NUMBER_TO_RUN = 100

columns = ['oldrevisionid', 'newrevisionid']  # Replace with your column names
# path to regular.csv and vandalism.csv
df = pd.read_csv('~/Desktop/Desktop - box mac/src/pioneer_boxuan/data_csvs/' +
                 PATH + '.csv', usecols=columns)

fromrev = df['oldrevisionid'].tolist()
torev = df['newrevisionid'].tolist()

# truncate to only first few
if TRUNCATE:
    del fromrev[NUMBER_TO_RUN:]
    del torev[NUMBER_TO_RUN:]
    RUN_RANGE = NUMBER_TO_RUN
else:
    RUN_RANGE = len(fromrev)


for i in range(RUN_RANGE):
    print('processing file ' + str(i) + ', ')
    print('with fromrev ' + str(fromrev[i]) +
          ', with torev ' + str(torev[i]) + '\n')

    filename = str(i) + '.txt'
    tmpdata = getdata(fromrev[i], torev[i])
    f = open(FOLDER_NAME + filename, "a")
    if (type(tmpdata) is str and tmpdata[:6] == 'ERROR:'):
        print('! Encountered ' + tmpdata[7:] + ' error\n')
        f.write(str(tmpdata))
    else:
        f.write('-----METADATA\n')
        for i in range(10):
            if (i == 8 and str(tmpdata[i]) == ''):
                f.write('<EMPTY>\n')
            else:
                f.write(str(tmpdata[i]) + '\n')

        f.write('-----ADDED\n')
        for i in range(len(tmpdata[10])):
            for j in tmpdata[10][i]:
                f.write(j+" ")

        f.write('\n-----DELETED\n')
        for i in range(len(tmpdata[11])):
            for j in tmpdata[11][i]:
                f.write(j+" ")
        f.close()
