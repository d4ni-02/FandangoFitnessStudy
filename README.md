# About scripts
- The repository reports all the scripts used during the project work.
- For the FANDANGO's implementation files, only the modified files are here reported.
- Missing files for the FANDANGO implementation are unchanged from the original version (https://github.com/fandango-fuzzer/fandango.git)

# Commands
## Execute the tests
- each time the $\alpha$ value was manually changed
- each file the output directory in Fitness-evaluation.py was manually changed
```bash
Path: fandango/evaluation
python3 Fitness-evaluation.py [time]
```

## Extract metrics
```bash
Path data-extraction/
python3 extract-stats.py -i [input dir] -o [output dir]

Path: project root
python3 data-extraction/A12-p_val.py
```