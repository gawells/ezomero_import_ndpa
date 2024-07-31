# ezomero_import_ndpa
Import ROIs from a Hammamutsu `.npda` file/s into Omero using the `ezomero` wrapper (mostly).

## Istallation 
`ezomero` doesn't seem to work with most current Python used by Omero server.
```
> conda create -n omero python=3.9 conda-forge::zeroc-ice==3.6.5 omero-py
> conda activate omero
> conda install argparse xmltodict deepdiff pathlib
```
## Usage
First create `~/.ezomero`
```
[DEFAULT]
OMERO_USER = user.name@institute.org
OMERO_GROUP = groupname
OMERO_HOST = omero.server
OMERO_PORT = 4064
OMERO_SECURE = True
```

### Importing
```
# Imporing a single file
> ~/src/ezomero_import_ndpa/ezomero_import_ndpa.py -f 'slide_file_name.ndpi.ndpa'
# Importing a list (of .ndpi/.npda)
>  ~/src/ezomero_import_ndpa/ezomero_import_ndpa.py -l list_of_WSIs.txt
```


## Assumptions
- Can take either `.npdi`, `.ndpa` names (or list thereof) as input and uses the stem for lookup in Omero.
- Only the first matching instance will have ROIs added
- Will check existing ROIs for duplicate geometry: if found old ROI well be deleted and the new one added from the `.ndpa` file. There seem to be some latency issues between script and server, sometimes the old ROI isn't deleted. Adding first and deleting next seems to mostly resolve this, as well as running on the server itself and not from another client.

