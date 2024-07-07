## Wikipedia Vandalism Detection 
Using the PAN-WVC-10 corpus: [_Potthast et. al._](https://downloads.webis.de/publications/papers/potthast_2010m.pdf)
\
```
python main.py >& results.txt &
tail -f results.txt
```
TODO:
- [ ] data from _getdata.py_ contains multiple line comments, throwing index out of bounds
- [ ] tune feature params
