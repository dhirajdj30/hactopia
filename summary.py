import fitz  # PyMuPDF for PDF handling
import pytesseract  # Tesseract for OCR
from PIL import Image
from transformers import pipeline
import io

summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    full_text = ""
    images = []

    # Loop through all pages in the PDF
    for page_num in range(doc.page_count):
        page = doc[page_num]
        # Extract text from the page
        full_text += page.get_text("text")
        
        # Extract images from the page
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            images.append(Image.open(io.BytesIO(image_bytes)))

    doc.close()
    return full_text, images

def extract_text_from_images(images):
    ocr_text = ""
    for img in images:
        ocr_text += pytesseract.image_to_string(img) + "\n"
    return ocr_text

# Function to chunk the text for summarization
def chunk_text(text, max_chunk_size=1024):
    words = text.split()
    chunks = []
    current_chunk = []
    current_length = 0

    for word in words:
        current_chunk.append(word)
        current_length += len(word) + 1  # +1 for space
        if current_length >= max_chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks

# Function to summarize each chunk of text
def summarize_chunks(chunks):
    summarized_text = ""
    for chunk in chunks:
        try:
            # Summarize each chunk
            summary = summarizer(chunk, max_length=150, min_length=25, do_sample=False)
            summarized_text += summary[0]['summary_text'] + " "
        except Exception as e:
            summarized_text += f"\nError in summarization: {str(e)}"
    return summarized_text

# Main function to process the uploaded PDF
def process_upload(file_path):
    try:
        # Extract text and images from the PDF
        text, images = extract_text_from_pdf(file_path)

        # Extract text from the images using OCR
        ocr_text = extract_text_from_images(images)

        # Combine text from the PDF and from OCR
        full_text = text + "\n" + ocr_text

        # Check if full_text is non-empty and large enough
        if len(full_text.strip()) == 0:
            return "No extractable text found in the PDF."

        # Chunk the text if it's too long
        chunks = chunk_text(full_text)

        # Summarize each chunk
        summary = summarize_chunks(chunks)

        return full_text, summary

    except Exception as e:
        return f"Error in processing PDF: {str(e)}", None