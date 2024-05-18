import yaml
import boto3
from configloader import ConfigLoader


class FromS3(ConfigLoader):

    def __init__(self, url):
        url_components = url.split('/')

        match url_components[0]:
            case "s3:":
                self._bucket = url_components[2]
                self._location = '/'.join(url_components[3:])
            case "https:":
                self._address = url_components[2]
                self._bucket = url_components[3]
                self._location = '/'.join(url_components[4:])
        print(f'{self._bucket} , {self._location}')
        super().__init__(path='FromS3')

    @property
    def configuration(self):
        s3_client = boto3.client('s3')
        response = s3_client.get_object(Bucket=self._bucket, Key=self._location)

        configuration = None
        try:
            configuration = yaml.safe_load(response["Body"])
        except yaml.YAMLError as exc:
            print(f"FromS3.configuration Exception: {exc}")

        return configuration
