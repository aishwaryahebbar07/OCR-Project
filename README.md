# Smart OCR System

## Project Overview
Smart OCR System is an academic project developed to extract text from multiple document formats using Optical Character Recognition (OCR). The system allows users to upload images, PDFs, Word documents, or text files and automatically extracts the text content.

The application provides a clean web interface where users can upload files, view extracted text, search within the extracted content, and download the results.

## Features
- Extract text from Images (JPG, PNG, JPEG)
- Extract text from PDF files
- Extract text from Word documents (.docx)
- Extract text from Text files (.txt)
- Drag and drop file upload interface
- Preview uploaded documents
- Confidence score display for OCR results
- Word and line count detection
- Document type detection
- Search and highlight words in extracted text
- Download extracted text as a .txt file

## Technologies Used
- Python
- Dash (Web Framework)
- OpenCV (Image Processing)
- Pytesseract (OCR Engine)
- NumPy
- PyPDF2
- python-docx
- PIL (Python Imaging Library)

## How the System Works
1. The user uploads a document (image, PDF, DOCX, or TXT).
2. The system processes the file.
3. If the file is an image, OCR is applied using Pytesseract.
4. If the file is PDF, DOCX, or TXT, text is extracted directly.
5. The extracted text is displayed in the interface.
6. The system calculates confidence score, word count, and line count.
7. Users can search within the text and download the results.

## How to Run the Project
1. Clone the repository  
git clone https://github.com/aishwaryahebbar07/OCR-Project.git

2. Navigate to the project folder  
cd OCR-Project

3. Install required libraries  
pip install dash opencv-python pytesseract numpy pillow PyPDF2 python-docx

4. Run the application  
python app.py

5. Open the application  
After running the program, open the local server link shown in the terminal (for example http://127.0.0.1:8050/) and upload a document to extract and analyze text.

## Project Interface
The system provides an interactive dashboard where users can upload documents, preview files, and view extracted text.

## Team Members
- Aishwarya D Hebbar
- Chaithra R
- Namrata Dhapte S

## Academic Project
This project was developed as part of an academic coursework project.