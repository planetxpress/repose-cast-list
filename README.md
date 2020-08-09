# Repose Cast List

Parses the published [Repose Cast List](https://www.welcometorepose.com/cast-list.html) and generates a sortable table of characters with associated PBs to a GCP storage bucket.

Environment variables:
* `BUCKET_NAME` - Name of the GCS bucket that files will be stored in.
* `CAST_FILE` - Name of the resulting HTML file that will be deployed to the GCS bucket.
