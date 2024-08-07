# ezomero_import_ndpa
Import ROIs from a Hammamatsu `.npda` file/s into Omero using [ezomero](https://github.com/TheJacksonLaboratory/ezomero?tab=readme-ov-file) (mostly).

## Installation 
`ezomero` doesn't seem to work with the most current Python used by Omero server.
```Shell
conda create -n omero python=3.9 conda-forge::zeroc-ice==3.6.5 omero-py
conda activate omero
conda install argparse xmltodict deepdiff pathlib # or pip install
```
## Usage
First create `~/.ezomero`
```INI
[DEFAULT]
OMERO_USER = user.name@institute.org
OMERO_GROUP = groupname
OMERO_HOST = omero.server
OMERO_PORT = 4064
OMERO_SECURE = True
```

### Importing
```Shell
conda activate omero
# Importing a single file
~/src/ezomero_import_ndpa/ezomero_import_ndpa.py -f slide_file_name.ndpi.ndpa
# Importing a list (of .ndpi/.npda)s
~/src/ezomero_import_ndpa/ezomero_import_ndpa.py -l list_of_WSIs.txt
```


## Notes
- Can take either `.ndpi`, `.ndpa` filenames (or list of) as input and uses the stem for lookup in Omero.
- Only the first matching instance will have ROIs added.
- Rulers are represented as double-headed arrows.
- Each Hammatsu ROI is created as a single shape ROI in Omero.
- Will check existing ROIs for duplicate geometry. If found the ROI will be updated with the new label and/or stroke color.
- The 'details' field in `.ndpa` is stored as 'description' in `ezomero`, but I don't know where this ends up in Omero.
  

