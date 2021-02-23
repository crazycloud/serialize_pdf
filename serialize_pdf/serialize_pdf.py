"""Main module."""
## pdf serialize code taken from -  https://github.com/JoshData/pdf-diff

import time
import logging
from lxml import etree
import json, subprocess, io, os
import re 
import requests
import zipfile
import shutil

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

PDFTOTEXT_PATH = "pdftotext"

          
class PDF:
    """
    Class methods to consume results from serialized pdf document
    """
    def __init__(self, txt, page_indexes, page_bboxes):
        self.txt = txt #
        self.page_indexes = page_indexes 
        self.page_bboxes = page_bboxes
        self.num_page = len(page_indexes)
        
    def get_context_line(self, start, end, context_window=(50,50)):
        context_sent = self.txt[start-context_window[0] : end + context_window[1]]
        start_sent = context_sent.rfind('.',0,context_window[0])
        end_sent = context_sent.rfind('.',-1*context_window[1],-1)
        start_sent = 0  if start_sent < 0 else start_sent
        end_sent = len(context_sent) if end_sent < 0 else end_sent
        if start-context_window[0] < 0:
            return 0 , end + context_window[1]    
        else:
            return start-context_window[0] + start_sent + 1, start-context_window[0] + end_sent

    def get_page_num(self,start, end):
        """
        based on the words indexes, get the page number
        """
        pages = [page for page, pos in self.page_indexes.items() if pos['start'] <= start and pos['end'] > start]
        if len(pages):
            return pages[0]
        else:
            return None
    
    def __simplify_bboxes(self,bboxes):
        """
        simplify multiple bboxes to a bigger enclosing box`
        """
        xmin= min([bbox['x'] for bbox in bboxes])
        ymin= min([bbox['y'] for bbox in bboxes])
        xmax= max([bbox['x'] + bbox['width'] for bbox in bboxes])
        ymax= max([bbox['y'] + bbox['height'] for bbox in bboxes])
        
        return [xmin, ymin, xmax-xmin,ymax-ymin]              

    def get_bboxes(self,start,end, normalize=True):
        """
        Get bbox enclosing the words from <start> and <end> index
        normalize - return normalized bbox values
        """
        page = self.get_page_num(start,end)
        bboxes =  [bbox for bbox in self.page_bboxes[str(page)] if (bbox['startIndex']>= start or  (bbox['startIndex'] +bbox['textLength'] > start > bbox['startIndex'])) and  bbox['startIndex'] < end]
        if len(bboxes):
            width = bboxes[0]['page']['width']
            height = bboxes[0]['page']['height']
            bboxes =self.__simplify_bboxes(bboxes)
            if not normalize:
                width = 1
                height = 1
            bboxes = [bboxes[0]/width, bboxes[1]/height, (bboxes[0] + bboxes[2])/width, (bboxes[1] + bboxes[3])/height]
            return bboxes
        return bboxes
    
    def get_kv(self,key, val_regex, group=0, normalize= False, return_context=False, context_window=(50,50)):
        """
        Search serialzed pdf document for <val_regex>
        """
        kvs = []
        for match in  re.finditer(val_regex, self.txt, flags=re.I):
            #print(match.group(1))
            match_start = match.start(group)
            match_end = match.end(group)
            if return_context:
                match_start, match_end = self.get_context_line(match.start(),match.end(),context_window)
            page = self.get_page_num(match_start, match_end)
            box = self.get_bboxes(start=match_start, end=match_end, normalize=normalize)
            kvs.append({'key': key,'val': self.txt[match_start:match_end],'start':match_start, 'end': match_end,'page': page,'bbox':box})
        
        return kvs
    
    def get_page_dim(self,page):
        """
        get page dimension for a specific page number
        """
        if len(self.page_bboxes[str(page)]):
            return (self.page_bboxes[str(page)][0]['page']['width'], self.page_bboxes[str(page)][0]['page']['height'])
        else:
            return (None,None)
        
    def get_enclosed_text(self,page, bbox, normalized=False):
        """
        Find words within the rectangle specified by <bbox [xmin, ymin, xmax, ymax]>
        normalized - if the bbox are normalized values
        """
        if normalized:
            width, height = self.get_page_dim(page)
        else:
            width, height = 1,1 
        
        words = [word_bbox for word_bbox in self.page_bboxes[str(page)] if 
         (word_bbox['x'] >= width * bbox[0]) and 
         (word_bbox['y']>= height*bbox[1]) and 
         word_bbox['x'] + word_bbox['width'] <= width * bbox[2] and 
         word_bbox['y'] + word_bbox['height'] <= height * bbox[3]]
        
        words = sorted(words, key = lambda x: (x['y'],x['x']))
        text = ''.join([word['text'] for word in words])
        return words, text
    
    def get_nearby_bboxes(self,page, bbox, r, normalized=False):
        """
        get neighbouring words by expanding bbox with relative dimensions specified by r
        """
        if normalized:
            width, height = self.get_page_dim(page)
        else:
            width, height = 1,1 
        
        delta =0
        words, _ = self.get_enclosed_text(page,[
             bbox[0]*width-((r[0]+delta)),
             bbox[1]*height-((r[1]+delta)),
             bbox[0]*width + bbox[2]*width +((r[2]+delta)),
             bbox[1]*height + bbox[3]*height+((r[3]+delta))
            ])
        
        #exclude the bbox boundary from the output
        words = [word for word in words if  (word['x'] < bbox[0]*width) or  ((word['x'] +word['width']) > bbox[2]*width) or ((word['y'] +word['height']) > bbox[3]*height) or (word['y'] < bbox[1]*height)]
        
        return words
    
def get_xml_dom(document_path):
    """
    Run the pdftotext process on the document and return xml with bboxes
    """
    if not shutil.which(PDFTOTEXT_PATH):
        logger.error("pdftotext not found")
        raise
        
    xml = subprocess.check_output([PDFTOTEXT_PATH,"-bbox-layout", document_path, "-"])

    # This avoids PCDATA errors
    codes_to_avoid = [ 0, 1, 2, 3, 4, 5, 6, 7, 8,11, 12,
                       14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, ]

    cleaned_xml = bytes([x for x in xml if x not in codes_to_avoid])
    dom = etree.fromstring(cleaned_xml)
    
    return dom
    
def pdf_to_bboxes(dom, top_margin=0, bottom_margin=100):

    """ 
    convert xml dom to dict object of words
    """
    
    words = []
    box_index = 0
    pdfdict = {
        "index": 1
    }
    
    for i, page in enumerate(dom.findall(".//{http://www.w3.org/1999/xhtml}page")):
    
        pagedict = {
            "number": i+1,
            "width": float(page.get("width")),
            "height": float(page.get("height"))
        }
    
        blocks_cols = [(b,0,0)for b in page.findall(".//{http://www.w3.org/1999/xhtml}block")]

        for block, col_index, _ in blocks_cols:
            for word in block.findall(".//{http://www.w3.org/1999/xhtml}word"):
                #print(word)
                if float(word.get("yMax")) < (top_margin/100.0)*float(page.get("height")):
                    continue
                if float(word.get("yMin")) > (bottom_margin/100.0)*float(page.get("height")):
                    continue

                words.append({
                        "index": box_index,
                        "pdf": pdfdict,
                        "page": pagedict,
                        "x": float(word.get("xMin")),
                        "y": float(word.get("yMin")),
                        "width": float(word.get("xMax"))-float(word.get("xMin")),
                        "height": float(word.get("yMax"))-float(word.get("yMin")),
                        "text": word.text
                        })
                box_index += 1
    return words    

def mark_eol_hyphens(boxes):
    # Replace end-of-line hyphens with discretionary hyphens so we can weed
    # those out later. Finding the end of a line is hard.
    box = None
    for next_box in boxes:
        if box is not None:
            if box['pdf'] != next_box['pdf'] or box['page'] != next_box['page'] \
                or next_box['y'] >= box['y'] + box['height']/2:
                # box was at the end of a line
                mark_eol_hyphen(box)
            yield box
        box = next_box
    if box is not None:
        # The last box is at the end of a line too.
        mark_eol_hyphen(box)
        yield box

def mark_eol_hyphen(box):
    if box['text'] is not None:
        if box['text'].endswith("-"):
            box['text'] = box['text'][0:-1] + "\u00AD"


    
def serialize(document_path):
    """
    Convert pdf document into json object with following attributes 
    {
    "page_bboxes" -  list of words with layout information
    "page_indexes" - word indexes in <text> field for each page
    "text" - full text of the document. removes next line characters
    }
    """
    #fout = open('test.log','w')
    start = time.time()
    dom = get_xml_dom(document_path)
    
    #time.time() - start
    box_generator = pdf_to_bboxes(dom)

    box_generator = mark_eol_hyphens(box_generator)

    boxes = []
    page_running_boxes=[]
    page_boxes={}
    text = []
    textlength = 0
    page_indexes = {}
    page_running_index = 1
    start_char_index = 0
    for run in box_generator:
        if run["text"] is None:
            continue

        normalized_text = run["text"].strip()

        # Ensure that each run ends with a space, since pdftotext
        # strips spaces between words. If we do a word-by-word diff,
        # that would be important.
        #
        # But don't put in a space if the box ends in a discretionary
        # hyphen. Instead, remove the hyphen.
        if normalized_text.endswith("\u00AD"):
            normalized_text = normalized_text[0:-1]
        else:
            normalized_text += " "

        run["text"] = normalized_text
        run["startIndex"] = textlength
        run["textLength"] = len(normalized_text)
        #boxes.append(run)
        
        if run["page"]["number"] != page_running_index:
            #print(run)
            page_indexes[page_running_index] = {'start' : start_char_index, 'end': run["startIndex"]}
            page_boxes[str(page_running_index)] = page_running_boxes
            start_char_index = run["startIndex"]
            page_running_index = run["page"]["number"]
            page_running_boxes = [run]
        else:
            page_running_boxes.append(run)
            
        text.append(normalized_text)
        page_boxes[str(page_running_index)] = page_running_boxes
        textlength += len(normalized_text)
    page_indexes[page_running_index]= {'start':start_char_index,'end': textlength}
    
    text = "".join(text)
    return PDF(text, page_indexes, page_boxes)
    #return {'text': text, 'page_indexes': page_indexes, 'page_bboxes' :page_boxes}
           
 