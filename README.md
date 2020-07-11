# ginji

_I will improve this later._

## Installation

1. Download the source code onto a Raspberry Pi, either by [downloading/extracting an archive](https://github.com/alycejenni/ginji/releases/latest) or by cloning the repo:
  ```sh
  git clone https://github.com/alycejenni/ginji.git
  ```
2. Install:
  ```sh
  cd ginji
  python setup.py install
  ```
3. Configure with a JSON file called `config.json` in the same directory (or point to another file by setting the environment variable `GINJI_CONFIG`). An example config:
  ```json
  {
    "root": "/home/username/catflap",
    "file_prefix": "anything-you-like",
    "connectors": {
      "s3": {
        "active": true,
        "host": "https://s3-object-host.com",
        "bucket": "bucket-name",
        "acl": "public-read"
      },
      "ifttt": {
        "active": true,
        "key": "your-api-key",
        "event": "event-name",
        "url": "https://maker.ifttt.com/trigger/event-name/with/key/your-api-key"
      },
      "drive": {
        "active": false,
        "scopes": "https://www.googleapis.com/auth/drive",
        "client_secret": ".credentials/client_secret.json",
        "app_name": "your-app-name",
        "credential_path": ".credentials/drive_credentials.json"
      }
    },
    "log_level": "debug"
  } 
  ```
  
  If you're using S3 (Amazon or otherwise), add `boto.cfg` to `.credentials`:
  ```
  [Credentials]
  aws_access_key_id = access-key
  aws_secret_access_key = secret
  ```

  If you want to use Google Drive, you need `.credentials/client_secret.json` and `.credentials/drive_credentials.json`, but I don't remember how I got those so you'll have to figure that one out yourself.
  
## Usage

```sh
# to print out all the options
ginji --help

# run the motion detection with the default options
ginji motion
```
