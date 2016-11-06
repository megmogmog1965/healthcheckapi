# healthcheckapi

## Usage

Install libs.

```
$ python --version
Python 2.7.12

$ sudo pip install flask requests psutil --upgrade
```

Then, run this script.

```
$ python healthcheckapi.py
```

You can access the url that returns status code 200 or 500. The code 200 means all conditions are satisfied.

* http://localhost:5000/

## Settings

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

|Keys||optional (default)|example|
|:-----------|:------------|:------------:|:------------|
|url|||/|
|port|||5000|
|status_code_healthy|||200|
|status_code_unhealthy|||500|
|target_process||||
||pid|YES|21540|
||name|YES|"Python"|
||matching|YES|"^.+/python .+$"|
|target_http||||
||url||https://localhost:80/foo/bar|
||healthy_status_codes|YES (200)|[ 200, 201 ]
||verify|YES (true)|false

## Author

[Yusuke Kawatsu]


[Yusuke Kawatsu]:https://github.com/megmogmog1965
