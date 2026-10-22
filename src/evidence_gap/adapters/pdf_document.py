def extract_pdf(path):
    import fitz
    doc=fitz.open(path)
    return [{"page":i+1,"text":p.get_text(),"extraction_method":"pymupdf_text"} for i,p in enumerate(doc)]
