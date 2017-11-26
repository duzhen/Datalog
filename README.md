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

## 3-Naive Evaluation
*   python datalog/datalog.py -p naive program/demo/3-naive.cdl
*   python datalog/datalog.py -p naive program/demo/3-2naive.cdl
    
## 4-Semi-Naive
*   python datalog/datalog.py -p semi-naive program/demo/4-semi-naive.cdl

## 5-Built-in
*   python datalog/datalog.py -p naive program/demo/5-builtins.cdl

## 6-Negation
*   python datalog/datalog.py -p naive program/demo/6-negation.cdl
*   python datalog/datalog.py -p naive program/demo/6-2negation.cdl

## 7-Performance/Others(trace,command query,optimization)
*   python datalog/datalog.py -t naive program/demo/7-trace.cdl
*   python datalog/datalog.py -p -x semi-naive program/demo/4-semi-naive.cdl
*   python datalog/datalog.py -p -c naive program/demo/7-others.cdl

*   same_clique(1,10)?
*   same_clique(1,11)?
*   same_clique(X, X)?
*   same_clique(X, X), X==1?

Reference:
*   https://github.com/ghxiao/nrdatalog2sql
*   https://github.com/DropSnorz/dataMink
*   https://github.com/wernsey/Jatalog
