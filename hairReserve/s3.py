import ConfigParser
import boto
import io
import os
from boto.s3.key import Key

config = ConfigParser.ConfigParser()
config.read("config.ini")

AWS_ACCESS_KEY = config.get('S3', 'AccessKey')
AWS_SECRET_ACCESS_KEY = config.get('S3', 'SecretKey')
S3_BUCKET = config.get('S3', 'Bucket')
S3_ITEM_PREFIX = config.get('S3', 'AndrewID')


# AWS_ACCESS_KEY = os.environ.get('AccessKey')
# AWS_SECRET_ACCESS_KEY = os.environ.get('SecretKey')
# S3_BUCKET = os.environ.get('Bucket')
# S3_ITEM_PREFIX = os.environ.get('AndrewID')
def s3_upload(uploaded_file, id):
    s3conn = boto.connect_s3(AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY)
    print AWS_SECRET_ACCESS_KEY
    bucket = s3conn.get_bucket(S3_BUCKET)

    k = Key(bucket)
    k.key = S3_ITEM_PREFIX + '-' + str(id)
    k.content_type = uploaded_file.content_type

    if hasattr(uploaded_file, 'temporary_file_path'):
        k.set_contents_from_filename(uploaded_file.temporary_file_path())
    else:
        k.set_contents_from_string(uploaded_file.read())

    k.set_canned_acl('public-read')

    return k.generate_url(expires_in=0, query_auth=False)


def s3_delete(id):
    s3conn = boto.connect_s3(AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY)
    bucket = s3conn.get_bucket(S3_BUCKET)

    k = Key(bucket)
    k.key = S3_ITEM_PREFIX + '-' + str(id)
    k.delete()
