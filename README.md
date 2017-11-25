# Datalog

## Requirements
*   Python 3
*   pip install -r requirements

Useage:
* python datalog/datalog.py -h
```
usage: datalog.py [-h] [-p] [-c] {naive,semi-naive} ... file

Datalog bottom-up evaluation implement by Python, support Naive, Semi-Naive, Built-Ins, stratified and negation

positional arguments:
  {naive,semi-naive}  commands
    naive             Bottom up evaluation with naive method search.
    semi-naive        Bottom up evaluation with semi-naive method search
  file                Datalog program file

optional arguments:
  -h, --help          show this help message and exit
  -p                  Prints parser result to file.
  -c                  Command to query.

```

## 1-Test Parser
*   python datalog/datalog.py -p naive program/demo/1-syntac.cdl
*   python datalog/datalog.py naive program/demo/datalog.cdl

## 2-Safety Check
*   python datalog/datalog.py naive program/demo/2-safety.cdl

## 3-Naive Evaluation

## 4-Semi-Naive

## 5-Built-in

## 6-Negation

## 7-Performance/Others(trace,command query,)
*   python datalog/datalog.py -p -c naive program/demo/7-others.pl

*   same_clique(1,10)?
*   same_clique(1,11)?
*   same_clique(X, X)?
*   same_clique(X, X), X==1?

Reference:
*   https://github.com/ghxiao/nrdatalog2sql
*   https://github.com/DropSnorz/dataMink
*   https://github.com/wernsey/Jatalog
