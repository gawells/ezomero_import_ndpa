#!/usr/bin/env python3
import ezomero as ez
from ezomero.rois import Rectangle,Line,Polyline,Polygon,Point,Ellipse
from omero import model
import numpy as np
import argparse
import xmltodict
from pathlib import Path
from deepdiff import DeepDiff


def find_image_id(conn,filename):   
    proj_ids = ez.get_project_ids(conn)
    # found = False
    for proj in proj_ids:
        ds_ids = ez.get_dataset_ids(conn,project=proj)
        for dset in ds_ids:
            image_ids = ez.get_image_ids(conn,dataset=dset)
            found_ids = ez.filter_by_filename(conn,image_ids,filename)
            
            if len(found_ids) > 0:          
                ndpi_index = np.min(found_ids)                      
                return(ndpi_index)


def get_slide_center(image):
    meta_data = image[0].loadOriginalMetadata() 
    for item in meta_data[1]:
        if type(item) is tuple:
            if item[0] == 'Slide center X (nm)':
                x = item[1]
            if item[0] == 'Slide center Y (nm)':
                y = item[1]
                return((x,y))


def get_imageDims(image):
    meta_data = image[0].loadOriginalMetadata() 
    for item in meta_data[1]:
        if type(item) is tuple:
            if item[0] == 'ImageLength':
                y = item[1]
            if item[0] == 'ImageWidth':
                x = item[1]
                return((x,y))


def hex_to_rgba(hcolor):
    hcolor = hcolor.lstrip('#')
    return tuple([int(hcolor[i:i+2], 16) for i in (0, 2, 4)]+[255])

    
def check_dupl_roi(roi_service,image_id,new_roi,conn=None):
    roi_ids = ez.get_roi_ids(conn, image_id)
    for roi_id in roi_ids:
        shape_ids = ez.get_shape_ids(conn, roi_id)
        for shape_id in shape_ids:
            shape = ez.get_shape(conn,shape_id)
            if type(shape) == type(new_roi) and DeepDiff(new_roi,shape) == {}:
                return True            
    return False


def convert_rois(fname,nmPerPxX,nmPerPxY,offset):
    omero_rois = []
    with open(fname, "rb") as file:
        xml = xmltodict.parse(file, dict_constructor=dict)

    # insert into list if only one annotation/roi
    if isinstance(xml['annotations']['ndpviewstate'],dict):
        annotations = [xml['annotations']['ndpviewstate']]
    else:
        annotations = xml['annotations']['ndpviewstate']

    for roi in annotations:     
        omero_roi = {}
        anno_type = roi['annotation']['@type']
        display_name = roi['annotation']['@displayname']
        omero_roi['line_color'] = roi['annotation']['@color']
        omero_roi['label'] = roi['title']
        omero_roi['description'] = roi['details']

        if anno_type == 'circle':
            omero_roi['type'] = 'ellipse'
            omero_roi['x'] = (int(roi['annotation']['x'])/nmPerPxX+offset['x'])
            omero_roi['y'] = (int(roi['annotation']['y'])/nmPerPxY+offset['y'])
            omero_roi['x_rad'] = int(roi['annotation']['radius'])/nmPerPxX
            omero_roi['y_rad'] = int(roi['annotation']['radius'])/nmPerPxY                      
            # set everything so that we can use deepdiff to check for duplicates.
            new_roi = ez.rois.Ellipse(x=omero_roi['x'],
                                y=omero_roi['y'],
                                x_rad=omero_roi['x_rad'],
                                y_rad=omero_roi['y_rad'],
                                stroke_color=hex_to_rgba(omero_roi['line_color']) ,
                                fill_color=(0,0,0,0),
                                stroke_width=1.0,
                                label=omero_roi['label']    )
            
            omero_rois.append((new_roi,omero_roi['description']))
        elif anno_type == 'freehand' and display_name == 'AnnotateRectangle':                   
            # (x,y) = top left corner, not centroid as for ellipse
            omero_roi['x'] = (int(roi['annotation']['pointlist']['point'][0]['x']))/nmPerPxX+offset['x']
            omero_roi['y'] = (int(roi['annotation']['pointlist']['point'][0]['y']))/nmPerPxY+offset['y']
            omero_roi['width'] = abs((int(roi['annotation']['pointlist']['point'][2]['x'])
                                -int(roi['annotation']['pointlist']['point'][0]['x']))/nmPerPxX)
            omero_roi['height'] = abs((int(roi['annotation']['pointlist']['point'][2]['y'])
                                -int(roi['annotation']['pointlist']['point'][0]['y']))/nmPerPxY)

            new_roi = ez.rois.Rectangle(x=omero_roi['x'],
                                y=omero_roi['y'],
                                width=omero_roi['width'],
                                height=omero_roi['height'],
                                stroke_color=hex_to_rgba(omero_roi['line_color']),
                                fill_color=(0,0,0,0),
                                stroke_width=1.0,
                                label=omero_roi['label']    )   

            omero_rois.append((new_roi,omero_roi['description']))
        elif anno_type == 'freehand' and display_name == 'AnnotateFreehandLine':            
            omero_roi['points'] = []
            for point in roi['annotation']['pointlist']['point']:
                omero_roi['points'].append((int(point['x'])/nmPerPxX+offset['x'],
                    int(point['y'])/nmPerPxY+offset['y']))

            new_roi = ez.rois.Polyline(points=omero_roi['points'],
                                stroke_color=hex_to_rgba(omero_roi['line_color']),
                                fill_color=(0,0,0,0),
                                stroke_width=1.0,
                                label=omero_roi['label'])

            omero_rois.append((new_roi,omero_roi['description']))           
        elif anno_type == 'freehand' and display_name == 'AnnotateFreehand':            
            omero_roi['points'] = []
            for point in roi['annotation']['pointlist']['point']:
                omero_roi['points'].append((int(point['x'])/nmPerPxX+offset['x'],
                    int(point['y'])/nmPerPxY+offset['y']))

            new_roi = ez.rois.Polygon(points=omero_roi['points'],
                                stroke_color=hex_to_rgba(omero_roi['line_color']),
                                fill_color=(0,0,0,0),
                                stroke_width=1.0,
                                label=omero_roi['label'])

            omero_rois.append((new_roi,omero_roi['description']))           
        elif anno_type == 'pointer' and display_name == 'AnnotatePointer':          
            omero_roi['x1'] = (int(roi['annotation']['x1'])/nmPerPxX+offset['x'])
            omero_roi['y1'] = (int(roi['annotation']['y1'])/nmPerPxY+offset['y'])
            omero_roi['x2'] = (int(roi['annotation']['x2'])/nmPerPxX+offset['x'])
            omero_roi['y2'] = (int(roi['annotation']['y2'])/nmPerPxY+offset['y'])

            new_roi = ez.rois.Line(x1=omero_roi['x1'],x2=omero_roi['x2'],
                                y1=omero_roi['y1'],y2=omero_roi['y2'],
                                stroke_color=hex_to_rgba(omero_roi['line_color']),
                                fill_color=(0,0,0,0),
                                stroke_width=1.0,
                                label=omero_roi['label'],markerStart='Arrow') 
                                # 'Arrow' seems to be the only string recognised for marker(Start/End)
                                # 'Circle' and 'Square' are ignored.

            omero_rois.append((new_roi,omero_roi['description']))           
        elif anno_type == 'pin' and display_name == 'AnnotatePin':          
            omero_roi['x'] = (int(roi['annotation']['x']))/nmPerPxX+offset['x']
            omero_roi['y'] = (int(roi['annotation']['y']))/nmPerPxY+offset['y']         

            new_roi = ez.rois.Point(x=omero_roi['x'],
                    y=omero_roi['y'],
                    stroke_width=1.0,
                    stroke_color=(255,255,255,0), # for some reason it gets set to this anyway, not yellow
                    fill_color=(0,0,0,0),
                    # are pins supposed to be invisilbe? Can't set colour in iviewer either
                    label=omero_roi['label']) 

            omero_rois.append((new_roi,omero_roi['description']))           

    return omero_rois


def files_exist(ndpi_fname,ndpa_fname):
    result = True
    ndpi = Path(ndpi_fname)
    ndpa = Path(ndpa_fname)
    if not ndpi.exists():
        print(f'File does not exist: {str(ndpi_fname)}')
        result = False
    if not ndpa.exists():
        print(f'File does not exist: {str(ndpa_fname)}')
        result = False
    return result


def ndp_names(fullname,conn):
    p = Path(fullname.strip('\npyt'))  
    if p.suffix == '.ndpa':
        ndpi_fname = str(p.parent)+'/'+p.stem
        ndpa_fname = str(p.parent)+'/'+p.name
    elif p.suffix == '.ndpi':
        ndpi_fname = str(p.parent)+'/'+p.name
        ndpa_fname = str(p.parent)+'/'+p.name+'.ndpa'
    else:
        return ('','')
        # conn.close()
        # raise Exception(f'Invalid filename 1: {fullname}')
    
    if files_exist(ndpi_fname,ndpa_fname):
        # convert ndpi path to name for lookup in omero
        ndpi_path = Path(ndpi_fname)
        ndpi_fname = ndpi_path.name

        return (ndpi_fname, ndpa_fname)
    else:
        return ('','')
        # conn.close()
        # raise Exception(f'Invalid filename 2: {fullname}')


def add_rois(conn,ndpi_fname,ndpa_fname,roi_service=None):  
    ndpi_index = find_image_id(conn,ndpi_fname)
    
    image = ez.get_image(conn,image_id=int(ndpi_index),no_pixels=True)
    
    # calculate nmPer pixel in x and y, can't seem to do this in ezomero with the metadata
    pixelsWrapper = image[0].getPrimaryPixels()
    sizeX = pixelsWrapper.getPhysicalSizeX()
    sizeY = pixelsWrapper.getPhysicalSizeY()
    nmPerPxX = model.LengthI(sizeX,model.enums.UnitsLength.NANOMETER).getValue()
    nmPerPxY = model.LengthI(sizeY,model.enums.UnitsLength.NANOMETER).getValue()

    slide_center = get_slide_center(image)
    image_dims = get_imageDims(image)
    offset = {}
    offset['x'] = image_dims[0]/2-slide_center[0]/nmPerPxX
    offset['y'] = image_dims[1]/2-slide_center[1]/nmPerPxY  
    
    rois = convert_rois(ndpa_fname,nmPerPxX,nmPerPxY,offset)

    for roi in rois:        
        shapes = list()
        shapes.append(roi[0])   
        if not check_dupl_roi(roi_service,int(ndpi_index),shapes[0],conn):
            ez.post_roi(conn, int(ndpi_index), shapes, description=roi[1])
        # how does description show up in Omero?


def main():     
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filename')
    parser.add_argument('-l', '--filelist')
    args = parser.parse_args()      
    conn = ez.connect()

    if args.filelist:
        with open(args.filelist) as flist:
            line = flist.readline()         
            while line != '':                               
                ndpi_fname,ndpa_fname = ndp_names(line,conn)
                if ndpi_fname != '':
                    print(f'Adding ROIs from {ndpa_fname}')
                    add_rois(conn,ndpi_fname,ndpa_fname)        
                line = flist.readline()
    elif args.filename: 
        ndpi_fname,ndpa_fname = ndp_names(args.filename,conn)
        if ndpi_fname != '':
            print(f'Adding ROIs from {ndpa_fname}')
            add_rois(conn,ndpi_fname,ndpa_fname,roi_service)        
    else:
        return
        
    conn.close() 

if __name__ == '__main__':
    main()
