import pdfplumber

def parse_pdf(file_path):
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "".join([page.extract_text() for page in pdf.pages])
        return text
    except Exception as e:
        return f"Error parsing file: {str(e)}"

file_path = "project dataset.pdf"

# Handle the result
parsed_text = parse_pdf(file_path)

# Optional: Save the result to a file
if not parsed_text.startswith("Error"):
    with open("parsed_text.txt", "w", encoding="utf-8") as f:
        f.write(parsed_text)


