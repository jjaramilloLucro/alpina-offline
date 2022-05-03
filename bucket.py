from google.cloud import storage
import google.auth
import os

credential_path = os.path.join('data','lucro-alpina-20a098d1d018.json')
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path
credentials_BQ, your_project_id = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
)

client = storage.Client()


def cors_configuration(bucket_name):
    """Set a bucket's CORS policies configuration."""
    # bucket_name = "your-bucket-name"

    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    bucket.cors = [
    {
        "origin": [
            "*"
        ],
        "responseHeader": [
            "Content-Type"
        ],
        "method": [
            "GET"
        ],
        "maxAgeSeconds": 3600
    }
]
    bucket.patch()

    print("Set CORS policies for bucket {} is {}".format(bucket.name, bucket.cors))
    return bucket

cors_configuration('lucro-alpina.appspot.com')