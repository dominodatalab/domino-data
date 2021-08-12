# data-access-sdk

## Datasource

Example usage:

```python

from data_access_sdk import datasource

redshift = datasource('Redshift-Warehouse')
res = redshift.execute('SELECT name AS label, value FROM my_table LIMIT 1000')

# Fetch one or many rows
row = res.fetchone()
rows = res.fetchmany(100)

# Load whole dataframe
df = res.to_pandas()

# Store dataframe to local file
res.to_file('/tmp/redshift-sample.csv', file_format='csv')
```

## Featureset

Example usage:

```python
# coming soon!
```
