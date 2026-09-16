# About scripts
- The repository reports all the scripts used during the project work.
- For the FANDANGO's implementation files, only the modified files are here reported.
- Missing files for the FANDANGO implementation are unchanged from the original version (https://github.com/fandango-fuzzer/fandango.git)

# About the tests
The directory eval-tests contains some of the custom grammar defined in testing FANDANGO.
Only the files test-person, test-math, test-byte are used in the study

# Commands
## Execute the tests
- each time the $\alpha$ value was manually changed (/fandango/src/fandango/evolution/evaluation.py)
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