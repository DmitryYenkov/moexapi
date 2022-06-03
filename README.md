## Moscow Exchange API functions

Example was taken from MOEX website:
https://fs.moex.com/files/6524

Code updated to python3 from python2

Usage:

```python

from moexapi import MicexISSClient
from tabulate import tabulate


iss = MicexISSClient()

index_dfs = iss.get_index()  # List of Dataframes

for key in index_dfs.keys():
    print('===============\n', key.upper(), '\n')
    print(index_dataframes[key].columns.to_list())
    print(tabulate(index_dataframes[key]))
    
```
and the output will be:

```

===============
 ENGINES 

['id', 'name', 'title']
-  ----  -------------  --------------------------------
0     1  stock          Фондовый рынок и рынок депозитов
1     2  state          Рынок ГЦБ (размещение)
2     3  currency       Валютный рынок
3     4  futures        Срочный рынок
4     5  commodity      Товарный рынок
5     6  interventions  Товарные интервенции
6     7  offboard       ОТС-система
7     9  agro           Агро
8  1012  otc            OTC Система
-  ----  -------------  --------------------------------
===============
 MARKETS 
 
```
etc.

# Implemented the following functions:


* iss.get_index()

  The tables of ENGINES, MARKETS, BOARDS, BOARGROUPS, DURATIONS, SECURITYTYPES, SECURITYGROUPS, SECURITYCOLLECTIONS.
  
* iss.get_securities_list()

  List of all securities (may take a long time to download).
  
* iss.get_history_listing(engine, market, board)

* iss.get_security_description(security)

* iss.get_correlations(engine, market, date)

  Correlation coefficients of the market
  
* iss.get_splits()

  Table of all splits and consolidations.
  
* iss.get_deviationcoeffs(engine, date)

* iss.get_share_hist(security, start_date, end_date, engine, market, board)

* iss.get_board_hist_date(date, engine, market, board)

# Note

Maybe some of functions require MOEX user ID and password, also proxy may be added, so it may look like this:

```python
iss = MicexISSClient(user='username', password='userpassword', proxy='proxy.url')
```

  




