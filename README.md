# healthcheckapi

## Usage

```
$ python healthcheckapi.py
```

## Settings.

You can edit ``config.json`` in root directory.

```json
{
  "url": "/",
  "port": 5000,
  "status_code_healthy": 200,
  "status_code_unhealthy": 500,
  
  "target_process": [
    {
      "pid": 21540,
      "name": "Python",
      "matching": "^.+/python .+$"
    }
  ],
  
  "target_http": [
    {
      "url": "https://localhost/foo/bar",
      "healthy_status_codes": [ 200, 201 ],
      "verify": false
    }
  ]
}
```

|tier1|tier2|optional (default)|example|
|:-----------|:------------|:------------:|:------------|
|url|||/|
|port|||5000|
|status_code_healthy|||200|
|status_code_unhealthy|||500|
|target_process||||
||pid|YES|21540|
||name|YES|Python|
||matching|YES|^.+/python .+$|
|target_http||||
||url||https://localhost/foo/bar|
||healthy_status_codes|YES (200)|[ 200, 201 ]
||verify|YES (true)|false

## Author

[Yusuke Kawatsu]


[Yusuke Kawatsu]:https://github.com/megmogmog1965
