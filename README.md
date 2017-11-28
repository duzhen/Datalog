# Datalog

## Requirements
*   Python 3
*   pip install -r requirements

Useage:
* python datalog/datalog.py -h
```
usage: datalog.py [-h] [-p] [-c] [-t] [-x] {naive,semi-naive} ... file

Datalog bottom-up evaluation implement by Python, support Naive, Semi-Naive,
Built-Ins and Stratified Negation

positional arguments:
  {naive,semi-naive}  commands
    naive             Bottom up evaluation with naive method search.
    semi-naive        Bottom up evaluation with semi-naive method search
  file                Datalog program file

optional arguments:
  -h, --help          show this help message and exit
  -p                  Prints parser result to file.
  -c                  Command to query.
  -t                  Trace evaluation progress.
  -x                  Turn on optimization mode.

```

## 1-Test Parser
*   python datalog/datalog.py -p naive program/demo/1-syntac.cdl

## 2-Safety Check
*   python datalog/datalog.py -p naive program/demo/2-safety.cdl

## 3-Naive&Semi-Naive Evaluation
*   python datalog/datalog.py -p semi-naive program/demo/3-linear.cdl
*   python datalog/datalog.py -p semi-naive program/demo/3-nonlinear.cdl
    
## 4-Built-in
*   python datalog/datalog.py -p naive program/demo/4-builtins.cdl

## 5-Negation
*   python datalog/datalog.py -p naive program/demo/5-stratification.cdl

## 6-Trace(trace,command query)
*   python datalog/datalog.py -t -c naive program/demo/6-trace.cdl

*   path(X, X)?
*   path(0, 2)?
*   path(X, X), X==1?

Reference:
*   https://github.com/ghxiao/nrdatalog2sql
*   https://github.com/DropSnorz/dataMink
*   https://github.com/wernsey/Jatalog
