from operator import itemgetter
from PIL import Image
import fitz
import io
import json
import sys

def fonts(doc, granularity=False):
    """Extracts fonts and their usage in PDF documents.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param granularity: also use 'font', 'flags' and 'color' to discriminate text
    :type granularity: bool
    :rtype: [(font_size, count), (font_size, count}], dict
    :return: most used fonts sorted by count, font style information
    """
    styles = {}
    font_counts = {}

    for page in doc:
        blocks = page.getText("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # block contains text
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if granularity:
                            identifier = "{0}_{1}_{2}_{3}".format(s['size'], s['flags'], s['font'], s['color'])
                            styles[identifier] = {'size': s['size'], 'flags': s['flags'], 'font': s['font'],
                                                  'color': s['color']}
                        else:
                            identifier = "{0}".format(s['size'])
                            styles[identifier] = {'size': s['size'], 'font': s['font']}

                        font_counts[identifier] = font_counts.get(identifier, 0) + 1  # count the fonts usage

    font_counts = sorted(font_counts.items(), key=itemgetter(1), reverse=True)

    if len(font_counts) < 1:
        raise ValueError("Zero discriminating fonts found!")

    return font_counts, styles


def font_tags(font_counts, styles):
    """Returns dictionary with font sizes as keys and tags as value.
    :param font_counts: (font_size, count) for all fonts occuring in document
    :type font_counts: list
    :param styles: all styles found in the document
    :type styles: dict
    :rtype: dict
    :return: all element tags based on font-sizes
    """
    p_style = styles[font_counts[0][0]]  # get style for most used font by count (paragraph)
    p_size = p_style['size']  # get the paragraph's size

    # sorting the font sizes high to low, so that we can append the right integer to each tag
    font_sizes = []
    for (font_size, count) in font_counts:
        font_sizes.append(float(font_size))
    font_sizes.sort(reverse=True)

    # aggregating the tags for each font size
    idx = 0
    size_tag = {}
    for size in font_sizes:
        idx += 1
        if size == p_size:
            idx = 0
            size_tag[size] = '<p>'
        if size > p_size:
            size_tag[size] = '<h{0}>'.format(idx)
        elif size < p_size:
            size_tag[size] = '<s{0}>'.format(idx)

    return size_tag


def headers_para(doc, size_tag):
    """Scrapes headers & paragraphs from PDF and return texts with element tags.
    :param doc: PDF document to iterate through
    :type doc: <class 'fitz.fitz.Document'>
    :param size_tag: textual element tags for each size
    :type size_tag: dict
    :rtype: list
    :return: texts with pre-prended element tags
    """
    header_para = []  # list with headers and paragraphs
    first = True  # boolean operator for first header
    previous_s = {}  # previous span
    imglist=[]
    corresp_list=[]
    for page in doc:
        blocks = page.getText("dict")["blocks"]
        for b in blocks:  # iterate through the text blocks
            if b['type'] == 0:  # this block contains text

                # REMEMBER: multiple fonts and sizes are possible IN one block

                block_string = ""  # text found in block
                for l in b["lines"]:  # iterate through the text lines
                    for s in l["spans"]:  # iterate through the text spans
                        if s['text'].strip():  # removing whitespaces:
                            if first:
                                previous_s = s
                                first = False
                                block_string = size_tag[s['size']] + s['text']
                            else:
                                if s['size'] == previous_s['size']:

                                    if block_string and all((c == "|") for c in block_string):
                                        # block_string only contains pipes
                                        block_string = size_tag[s['size']] + s['text']
                                    if block_string == "":
                                        # new block has started, so append size tag
                                        block_string = size_tag[s['size']] + s['text']
                                    else:  # in the same block, so concatenate strings
                                        block_string += " " + s['text']

                                else:
                                    header_para.append(block_string)
                                    block_string = size_tag[s['size']] + s['text']

                                previous_s = s

                    # new block started, indicating with a pipe
                    block_string += "|"

                header_para.append(block_string)
                if '<h4' in block_string:
                    corresp_list.append(block_string)
            if b['type']==1:
                # print(b['bbox'])
                # print(b)
                # print(b['image'])
                # base_image = doc.extractImage(b['xres'])
                # print(base_image)
                image_bytes = b["image"]
                if len(corresp_list)!=0:
                    # corresp_list.append(image_bytes)
                    imglist.append(image_bytes)

                # get the image extension
                # image_ext = base_image["ext"]
                # load it to PIL    
                # image = Image.open(io.BytesIO(image_bytes))
                # image = Image.open(io.BytesIO(b['image']))
                # image.show()


    return header_para,imglist, corresp_list


def main():

    file = sys.argv[1]
    document = file
    doc = fitz.open(document)

    font_counts, styles = fonts(doc, granularity=False)

    # print(font_counts)

    size_tag = font_tags(font_counts, styles)
    # print(size_tag)

    elements, imglist, corresp_list = headers_para(doc, size_tag)
    for i in range(len(imglist)):
        print(corresp_list[i])
        # image = Image.open(io.BytesIO(imglist[i]))
        imgname = str(corresp_list[i])
    #     imgname = imgname.replace('<h3>','')
    #     imgname = imgname.replace('|','')
    #     image.save('images/'+ imgname + '.png')
    # image = Image.open(io.BytesIO(imglist[2]))
    # image.show()

    '''
    for e in elements:
        # print(e)
        # print(e[0])
        if e != '' and e[0]=='<':
            # print(e)
            e = e.split('>')
            orig_e = e[1]
            orig_e = orig_e.replace('|','')
            e = e[0]
            # print(e)
            e = e.split('<')
            # print(e)
            if e[1] == 'p':
                print(orig_e)
            # break
    '''
    '''
    for page in doc:
        for line in page.getText("html").splitlines():
            # if '<p' in line:
                print(line)
                break
    '''
    # with open("doc.json", 'w') as json_out:
    #     json.dump(elements, json_out)

if __name__ == '__main__':
    main()